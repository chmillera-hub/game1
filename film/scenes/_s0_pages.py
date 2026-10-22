"""_s0_pages.py -- private helper for s0_prologue.py: the prologue's own storybook pages.

The bard's book (storybook.Book) is filled with pages painted for THIS film's song: every
illustration here is an sb.Illustration (static art cached per resolution bucket, life drawn per
frame) whose life is SYNCED TO THE LYRICS -- it is handed the scene's event times (EV, computed by
the scene from song_timing.json word times) and acts on them: windows light on "kingdom of stone",
doors slam on "lock", shutters latch on "latch", the painted dragon sighs on "sigh" and waves on
"waved", the stone-seller lifts a rune-stone on "stone"...

The verse text is written onto the page by an invisible quill as it is sung (VerseText), and each
page is a composite callable (PageArt) so the text and the living picture are part of the page
itself -- they turn with it when the page turns (no overlay pops).

Everything is drawn with the library's painter's toolkit (sb.wash / ink / gild / hatch, IM FELL /
Uncial lettering, sb.PIGMENTS) so these pages match the established storybook look; nothing here
edits film/lib.
"""

import math
import random

import cairocffi as cairo

from film.lib import core, fx
from film.lib import storybook as sb
from film.lib import characters as ch
from film.lib.characters import base as B
from film.lib.core import clamp, lerp, smooth

TAU = math.tau
P = sb.PIGMENTS
INK = sb.INK


# ----------------------------------------------------------------------------------------
# the song clock: word times straight from film/assets/song/song_timing.json
# ----------------------------------------------------------------------------------------

def _norm(w):
    return "".join(c for c in w.lower() if c.isalpha() or c == "'" or c == "’").replace("’", "'")


class Song:
    """Lyric word timing for the prologue (local scene time == song time: s0_song starts at 0)."""

    def __init__(self):
        tm = ch.bard_song_timing()
        P_ = tm["prologue"] if tm else {"lines": [], "marks": {}, "beats": [], "downbeats": []}
        self.lines = {ln["id"]: ln for ln in P_.get("lines", [])}
        self.marks = dict(P_.get("marks", {}))
        self.beats = list(P_.get("beats", []))
        self.downbeats = list(P_.get("downbeats", []))
        self.strokes = list(P_.get("strokes", []))

    def words(self, lid):
        ln = self.lines.get(lid)
        if not ln:
            return []
        return [(w["w"], float(w["start"]), float(w["end"])) for w in ln.get("words", [])]

    def word(self, lid, word, nth=0, default=None):
        """(start, end) of the nth occurrence of `word` in line lid."""
        k = 0
        for w, a, b in self.words(lid):
            if _norm(w) == _norm(word):
                if k == nth:
                    return a, b
                k += 1
        return default

    def at(self, lid, word, nth=0, default=0.0):
        r = self.word(lid, word, nth)
        return r[0] if r else default


SONG = Song()

LATCH_LEAD, LATCH_STEP = 0.1, 0.075            # the shutter run: starts just before "latch", 75 ms apart
LATCH_CLOSE, LATCH_BAR = 0.26, 0.18           # each pair swings shut in 0.26 s, then its bar drops in 0.18 s
PADLOCK_DELAY = 0.12                          # the heart padlock snaps shut this long after its door slams


# ----------------------------------------------------------------------------------------
# small painter's helpers (on top of sb.wash / sb.ink / sb.gild / sb.hatch)
# ----------------------------------------------------------------------------------------

def _poly(cr, pts):
    cr.new_path()
    core.polygon(cr, pts)
    return B.Path(cr)


def spiral_pts(cx, cy, r0, r1, turns=1.6, n=22, a0=0.0, sx=1.0, sy=1.0, cw=1):
    """Points of an Archimedean spiral (Kells curl) from radius r0 (centre) out to r1."""
    pts = []
    for i in range(n + 1):
        u = i / n
        a = a0 + cw * u * turns * TAU
        r = lerp(r0, r1, u)
        pts.append((cx + math.cos(a) * r * sx, cy + math.sin(a) * r * sy))
    return pts


def crescent_pts(cx, cy, r, ox, oy, r2, n=40):
    """Outline of a crescent: the disc (cx, cy, r) minus the disc (cx+ox, cy+oy, r2)."""
    def inside2(px, py):
        return (px - cx - ox) ** 2 + (py - cy - oy) ** 2 < r2 * r2
    outer = [(cx + math.cos(TAU * k / n) * r, cy + math.sin(TAU * k / n) * r) for k in range(n)]
    keep = [not inside2(*p) for p in outer]
    if all(keep) or not any(keep):
        return outer
    # rotate so the kept run starts at index 0
    s = next(i for i in range(n) if keep[i] and not keep[i - 1])
    outer = outer[s:] + outer[:s]
    keep = keep[s:] + keep[:s]
    run = [p for p, k in zip(outer, keep) if k]
    a0 = math.atan2(run[-1][1] - cy - oy, run[-1][0] - cx - ox)
    a1 = math.atan2(run[0][1] - cy - oy, run[0][0] - cx - ox)
    while a1 > a0:
        a1 -= TAU
    inner = [(cx + ox + math.cos(lerp(a0, a1, k / 16.0)) * r2, cy + oy + math.sin(lerp(a0, a1, k / 16.0)) * r2)
             for k in range(1, 16)]
    return run + inner


def gold_star(cr, x, y, r, shimmer=0.5, points=8, inner=0.42, rot=0.0):
    pts = []
    for i in range(points * 2):
        a = rot + math.pi * i / points - math.pi / 2
        rr = r if i % 2 == 0 else r * inner
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    sb.gild(cr, pts, shimmer=shimmer, outline=max(0.15, r * 0.06))


def stipple(cr, x0, y0, x1, y1, n, color, alpha, r=(0.25, 0.6), seed=0):
    rng = random.Random(seed)
    core.src(cr, color, alpha)
    for _ in range(n):
        core.circle(cr, rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(*r))
    cr.fill()


def soft_glow(cr, x, y, r, color, alpha):
    """A painted (OVER) glow -- light in the paint, not on the lens."""
    fx.glow(cr, x, y, r, color, alpha, additive=False)


def lit_window(cr, x, y, w, h, lit, seed=0, arch=True, frame=INK):
    """A small leaded window: dark night glass, warm lamplight when lit (0..1)."""
    pts = [(x, y + h), (x, y + w * 0.5)] if arch else [(x, y + h), (x, y)]
    if arch:
        for k in range(1, 8):
            a = math.pi + math.pi * k / 8
            pts.append((x + w * 0.5 + math.cos(a) * w * 0.5, y + w * 0.5 + math.sin(a) * w * 0.5))
        pts += [(x + w, y + w * 0.5), (x + w, y + h)]
    else:
        pts += [(x + w, y), (x + w, y + h)]
    glass = core.mix("#1c2244", "#ffcf6a", 0.92 * lit)
    p = sb.wash(cr, pts, glass, 0.97, 0.25, w=0.5)
    if lit > 0.02:
        cr.save()
        p.add(cr)
        cr.clip()
        g = core.radial(x + w * 0.5, y + h * 0.65, max(w, h) * 0.8,
                        [(0.0, core.alpha("#fff3c4", 0.9 * lit)), (1.0, core.alpha("#ffb14a", 0.0))])
        cr.set_source(g)
        cr.paint()
        cr.restore()
    # leading: a diamond lattice
    cr.save()
    p.add(cr)
    cr.clip()
    lines = []
    step = max(1.6, w * 0.45)
    k = -h
    while k < w + h:
        lines.append([(x + k, y), (x + k + h, y + h)])
        lines.append([(x + k + h, y), (x + k, y + h)])
        k += step
    B.detail_lines(cr, lines, 0.22, "#2a1d14", 0.55, taper=(1.0, 1.0, 1.0))
    cr.restore()
    sb.ink_outline(cr, p, 0.45, frame, 0.85)
    return p


# ----------------------------------------------------------------------------------------
# painted folk: little storybook creatures (never human), opaque washes + iron-gall ink
# ----------------------------------------------------------------------------------------

FOLK = {
    "goblin": dict(skin="#8faa62", cloak="#7a4e30", trim="#c79a62", hood=False, ears="goblin", nose=1.0, h=1.0),
    "elf": dict(skin="#e8d3c0", cloak="#3f6e5c", trim="#c9b48a", hood=True, ears="elf", nose=0.2, h=1.12),
    "mouse": dict(skin="#b3a596", cloak="#8f3236", trim="#d9b77c", hood=False, ears="mouse", nose=0.8, h=0.82,
                  tail=True),
    "dwarf": dict(skin="#d9a582", cloak="#a8622f", trim="#5e3b25", hood=False, ears="dwarf", nose=0.5, h=0.86,
                  beard="#e3ddd2", cap="#4b5d8a"),
    "kobold": dict(skin="#c97446", cloak="#34539c", trim="#d8b25e", hood=True, ears="kobold", nose=1.2, h=0.92,
                   tail=True),
    "hare": dict(skin="#cbb79a", cloak="#6b5a8a", trim="#d6c08e", hood=False, ears="hare", nose=0.4, h=0.95),
    "frog": dict(skin="#86a95a", cloak="#5d4a8c", trim="#d8b25e", hood=False, ears="frog", nose=0.0, h=0.9),
}


def pfolk(cr, x, y, s=1.0, kind="goblin", t=0.0, facing=1, walk=0.0, phase=0.0, hurry=0.0, away=0.0,
          look=0.0, reach=0.0, lantern=False, lantern_lit=1.0, alpha=1.0, seed=0, hood=None, bundle=None,
          lift=0.0, hold=None, shrug=0.0):
    """A painted creature figure standing at (x, y) (feet), ~38*s units tall, facing +1 right / -1
    left. walk 0..1 + phase (legs, bob); hurry 0..1 (leans, head down, hood up); away 0..1 (turned
    away from us: the face hides behind the hood/head); look -1..1 glance (head turned toward the
    viewer side); reach 0..1 the front arm goes out (a door, a latch); lantern: carries one (lit).
    alpha < 1 fades the whole figure (stepping into a doorway)."""
    F = FOLK.get(kind, FOLK["goblin"])
    if alpha <= 0.01:
        return None
    if alpha < 0.999:
        cr.push_group()
    hs = F["h"]
    ph = phase * TAU
    bob = -abs(math.sin(ph)) * 1.2 * walk
    lean = 0.10 * hurry + 0.05 * walk
    cr.save()
    cr.translate(x, y)
    cr.scale(s * facing, s)
    ink_c = INK
    # --- legs + boots (behind the cloak hem)
    for k in (-1, 1):
        sw = math.sin(ph + (0.0 if k < 0 else math.pi)) * 4.2 * walk
        up = max(0.0, math.cos(ph + (0.0 if k < 0 else math.pi))) * 2.2 * walk
        lx = k * 2.4 + sw
        leg = [(k * 2.2 - 1.6, -10.0 * hs), (k * 2.2 + 1.6, -10.0 * hs), (lx + 1.4, -2.0 - up), (lx - 1.4, -2.0 - up)]
        sb.wash(cr, leg, core.shade(F["cloak"], 0.45), 0.98, 0.0)
        boot = [(lx - 2.4, -3.4 - up), (lx + 1.4, -3.6 - up), (lx + 4.2, -1.6 - up), (lx + 4.0, -0.2 - up),
                (lx - 2.6, -0.2 - up)]
        pb = sb.wash(cr, boot, "#3a281c", 0.98, 0.0)
        sb.ink_outline(cr, pb, 0.45, ink_c, 0.8)
    cr.translate(0.0, bob)
    cr.rotate(lean)
    ch_ = 23.0 * hs
    # --- tail
    if F.get("tail"):
        tw = math.sin(t * 2.3 + seed) * 2.0 + walk * math.sin(ph) * 1.5
        sb.ink(cr, [(-5.0, -8.0), (-11.0, -5.5 + tw), (-15.5, -9.0 + tw), (-16.5, -12.0 + tw * 0.6)], 1.4,
               F["skin"], 1.0, (1.0, 0.8, 0.25))
    # --- back arm (swinging)
    sw_b = -math.sin(ph) * 2.8 * walk
    sb.ink(cr, [(-1.5, -ch_ * 0.72), (-3.0 + sw_b, -ch_ * 0.42), (-2.0 + sw_b, -ch_ * 0.3)], 2.6,
           core.shade(F["cloak"], 0.25), 1.0, (1.0, 1.0, 0.9))
    # --- the cloak: a bell, a darker hem band, a lit flank, a fold
    flare = 1.0 + 0.08 * walk * math.sin(ph * 2.0)
    cloak = [(-8.2 * flare, -6.5), (-6.4, -ch_ * 0.62), (-4.2, -ch_ * 0.93), (0.0, -ch_ - 0.6), (4.2, -ch_ * 0.93),
             (6.4, -ch_ * 0.62), (8.6 * flare, -6.0), (5.0, -4.6), (0.0, -5.0), (-4.6, -4.4)]
    pc = sb.wash(cr, cloak, F["cloak"], 0.99, 0.5, smooth_t=0.75, w=0.55)
    cr.save()
    pc.add(cr)
    cr.clip()
    core.src(cr, core.tint(F["cloak"], 0.22), 0.55)          # the lit flank (light from upper left)
    cr.new_path()
    core.smooth_closed(cr, [(-9.0, -5.0), (-6.6, -ch_ * 0.6), (-3.5, -ch_ * 0.92), (-1.5, -ch_ * 0.6),
                            (-3.0, -5.0)], 0.8)
    cr.fill()
    core.src(cr, core.shade(F["cloak"], 0.35), 0.5)            # hem band
    cr.rectangle(-10, -9.0, 20, 6.0)
    cr.fill()
    core.src(cr, F["trim"], 0.85)
    cr.rectangle(-10, -9.6, 20, 1.0)
    cr.fill()
    cr.restore()
    sb.ink(cr, [(1.5, -ch_ * 0.55), (2.6, -ch_ * 0.3), (2.2, -8.0)], 0.5, ink_c, 0.45)
    sb.ink_outline(cr, pc, 0.6, ink_c, 0.85)
    if bundle:
        bx, by = -5.5, -ch_ * 0.75
        pbd = sb.wash(cr, [(bx - 3.5, by), (bx + 3.0, by - 1.0), (bx + 3.6, by + 5.0), (bx - 3.0, by + 5.5)], bundle,
                      0.98, 0.3)
        sb.ink_outline(cr, pbd, 0.45, ink_c, 0.8)
    # --- head
    hy = -ch_ - 4.6
    cr.save()
    cr.translate(0.8 - 0.8 * away, hy + 1.2 * hurry)
    cr.rotate(0.22 * hurry - 0.08 * look)
    sk = F["skin"]
    hood_on = F["hood"] if hood is None else hood
    ears = F["ears"]
    # ears behind the head
    if ears in ("goblin", "elf") and not (hood_on and ears == "elf" and away > 0.5):
        L_ = 9.5 if ears == "goblin" else 8.0
        for sgn in (-1.0, 1.0):
            e = [(sgn * 3.2, -2.4), (sgn * (3.6 + L_), -4.6 - (1.5 if ears == "elf" else 0.0)), (sgn * 3.6, 0.6)]
            pe = sb.wash(cr, e, sk, 0.99, 0.3)
            sb.ink_outline(cr, pe, 0.45, ink_c, 0.75)
    elif ears == "mouse":
        for ex in (-3.0, 2.6):
            pe = sb.wash(cr, [(ex + math.cos(a) * 3.0, -5.6 + math.sin(a) * 3.0) for a in [i * TAU / 10 for i in range(10)]],
                         sk, 0.99, 0.3)
            sb.ink_outline(cr, pe, 0.45, ink_c, 0.75)
            sb.wash(cr, [(ex + math.cos(a) * 1.6, -5.6 + math.sin(a) * 1.6) for a in [i * TAU / 10 for i in range(10)]],
                    P["rose"], 0.8, 0.0)
    elif ears == "hare":
        for ex, a0 in ((-1.6, -0.25), (1.8, 0.2)):
            e = [(ex - 1.2, -3.0), (ex - 2.0 + a0 * 10, -13.0), (ex + 0.4 + a0 * 10, -14.0), (ex + 1.4, -3.0)]
            pe = sb.wash(cr, e, sk, 0.99, 0.3, smooth_t=0.6)
            sb.ink_outline(cr, pe, 0.45, ink_c, 0.75)
    # the face (or the back of the head when turned away)
    if ears == "frog":
        # a broad flat frog head, bulging eyes on top, a long wide mouth
        face = [(-5.0, -2.6), (-2.0, -4.6), (3.6, -4.4), (6.4, -1.4), (5.8, 1.8), (1.0, 3.2), (-4.2, 2.4)]
    else:
        face = [(-4.4, -3.2), (-1.0, -6.0), (3.6, -5.2), (5.0, -1.4), (4.4, 2.2), (0.6, 3.6), (-3.6, 2.6)]
    pf = sb.wash(cr, face, sk if away < 0.5 else core.shade(sk, 0.15), 0.99, 0.35, smooth_t=0.8, w=0.5)
    sb.ink_outline(cr, pf, 0.5, ink_c, 0.8)
    if ears == "frog" and away < 0.5:
        sb.wash(cr, [(-3.0, 1.0), (5.0, 0.4), (4.4, 2.4), (-2.6, 2.6)], core.tint(sk, 0.35), 0.8, 0.0, smooth_t=0.7)
        for k_, (ex, ey, er) in enumerate(((-0.6, -4.6, 2.3), (3.6, -4.3, 2.2))):
            pe = sb.wash(cr, [(ex + math.cos(a) * er, ey + math.sin(a) * er) for a in [i * TAU / 12 for i in range(12)]], sk,
                         0.99, 0.3)
            sb.ink_outline(cr, pe, 0.45, ink_c, 0.85)
            cr.new_path()
            core.circle(cr, ex + 0.25 + 0.5 * look, ey - 0.2, er * 0.62)
            core.src(cr, "#f6eed8")
            cr.fill()
            cr.new_path()
            core.ellipse(cr, ex + 0.45 + 0.7 * look, ey - 0.1, er * 0.22, er * 0.36)
            core.src(cr, "#1d120c")
            cr.fill()
            if hurry > 0.3 or shrug > 0.3:     # heavy lids: a weary shopkeeper's shrug
                sb.wash(cr, [(ex - er, ey - 0.3), (ex - er * 0.6, ey - er * 0.9), (ex + er * 0.6, ey - er * 0.9),
                             (ex + er, ey - 0.3)], sk, 0.99, 0.0)
        sb.ink(cr, [(-3.4, 1.2), (0.8, 1.9), (5.4, 0.6)], 0.5, ink_c, 0.85)
    elif away < 0.5:
        nose = F["nose"]
        if nose > 0.1:
            sn = [(3.4, -1.8), (5.0 + 3.6 * nose, -0.6 + (1.0 if ears == "goblin" else 0.0)), (3.4, 1.4)]
            ps = sb.wash(cr, sn, sk, 0.99, 0.3, smooth_t=0.5)
            sb.ink_outline(cr, ps, 0.45, ink_c, 0.75)
            if ears == "mouse":
                sb.ink(cr, [(5.6, -0.2), (9.0, -1.6)], 0.25, ink_c, 0.6)
                sb.ink(cr, [(5.6, 0.4), (9.2, 0.8)], 0.25, ink_c, 0.6)
        # the eye: a bead with a glint; a heavy lid when hurrying (head down, not looking)
        ex, ey = 1.6 + 0.8 * look, -1.6
        cr.new_path()
        core.ellipse(cr, ex, ey, 0.95, 1.15)
        core.src(cr, "#1d120c")
        cr.fill()
        cr.new_path()
        core.circle(cr, ex + 0.35, ey - 0.4, 0.32)
        core.src(cr, "#fff6e0", 0.9)
        cr.fill()
        if hurry > 0.3:
            sb.ink(cr, [(ex - 1.3, ey - 0.6), (ex + 1.3, ey - 0.9)], 0.55, ink_c, 0.85 * min(1.0, hurry * 1.5))
    if F.get("beard") and away < 0.5:
        bd = [(-3.2, 0.4), (4.6, 0.0), (5.2, 4.0), (2.0, 9.5), (-1.6, 9.0), (-3.8, 4.0)]
        pb = sb.wash(cr, bd, F["beard"], 0.99, 0.3, smooth_t=0.7)
        sb.ink_outline(cr, pb, 0.45, ink_c, 0.7)
        sb.ink(cr, [(0.5, 2.0), (0.8, 7.0)], 0.3, ink_c, 0.4)
    if F.get("cap"):
        cap = [(-4.8, -3.6), (-2.0, -6.8), (2.0, -9.0), (6.0, -13.0 - 1.5 * math.sin(t * 2.0 + seed)), (4.0, -6.0),
               (5.0, -4.2)]
        pcp = sb.wash(cr, cap, F["cap"], 0.99, 0.4, smooth_t=0.6)
        sb.ink_outline(cr, pcp, 0.5, ink_c, 0.8)
    if hood_on or hurry > 0.6:
        hood_c = F["cloak"]
        if away >= 0.5:
            hd = [(-5.4, 2.6), (-5.6, -4.0), (-1.0, -7.6), (4.0, -6.6), (5.4, -2.0), (5.0, 2.8)]
        else:
            hd = [(-5.4, 2.6), (-5.6, -4.0), (-1.4, -7.8), (3.6, -7.0), (5.2, -3.6), (2.8, -4.4), (-1.6, -3.4),
                  (-3.4, 2.2)]
        ph_ = sb.wash(cr, hd, hood_c, 0.99, 0.45, smooth_t=0.7, w=0.5)
        sb.ink_outline(cr, ph_, 0.55, ink_c, 0.85)
        if ears in ("elf", "goblin") and away < 0.5:
            for sgn in (-1.0,):
                e = [(sgn * 4.0, -3.5), (sgn * 11.0, -6.0), (sgn * 4.6, -1.0)]
                pe = sb.wash(cr, e, sk, 0.99, 0.3)
                sb.ink_outline(cr, pe, 0.45, ink_c, 0.75)
    cr.restore()
    # --- front arm (reaching / holding a lantern / swinging / lifting a ware up high)
    sw_f = math.sin(ph) * 2.8 * walk
    sx, sy = 2.2, -ch_ * 0.74 - 1.6 * shrug
    hx = lerp(3.4 + sw_f, 10.5, reach)
    hy_ = lerp(-ch_ * 0.36, -ch_ * 0.62, reach)
    if lift > 0:
        hx = lerp(hx, 7.5, lift)
        hy_ = lerp(hy_, -ch_ - 9.0, lift)
    if shrug > 0:
        hx = lerp(hx, 9.5, shrug)
        hy_ = lerp(hy_, -ch_ * 0.98, shrug)
    if lantern:
        hx, hy_ = lerp(5.0, 8.0, reach), -ch_ * 0.45
    sb.ink(cr, [(sx, sy), ((sx + hx) * 0.5 + 0.6, (sy + hy_) * 0.5 + 1.2), (hx, hy_)], 2.8, F["cloak"], 1.0,
           (1.0, 1.0, 0.9))
    if hold is not None:
        hold(cr, hx + 0.6, hy_ - 3.4)
    cr.new_path()
    core.circle(cr, hx + 0.6, hy_ + 0.2, 1.35)
    core.src(cr, F["skin"])
    cr.fill()
    sb.ink_outline(cr, _poly(cr, [(hx + 0.6 + math.cos(a) * 1.35, hy_ + 0.2 + math.sin(a) * 1.35)
                                  for a in [i * TAU / 10 for i in range(10)]]), 0.35, ink_c, 0.7)
    if shrug > 0.02:                          # the other hand comes up too: "what can you do?"
        bx_, by_ = -8.0, -ch_ * 0.92
        sb.ink(cr, [(-2.0, -ch_ * 0.74 - 1.6 * shrug), (-6.0, -ch_ * 0.66), (bx_, by_ - 2.0 * shrug)], 2.6,
               core.shade(F["cloak"], 0.1), shrug, (1.0, 1.0, 0.9))
        cr.new_path()
        core.circle(cr, bx_ - 0.4, by_ - 2.2 * shrug, 1.3)
        core.src(cr, F["skin"], shrug)
        cr.fill()
    lamp = None
    if lantern:
        sway = 0.25 * math.sin(t * 2.6 + seed) + 0.15 * walk * math.sin(ph)
        cr.save()
        cr.translate(hx + 0.6, hy_ + 0.8)
        cr.rotate(sway)
        sb.ink(cr, [(0.0, 0.0), (0.0, 2.2)], 0.4, "#2e2a28", 1.0)
        if lantern_lit > 0:
            soft_glow(cr, 0.0, 5.0, 9.0, "#ffc46a", 0.45 * lantern_lit)
        body = [(-2.0, 2.2), (2.0, 2.2), (2.5, 4.4), (1.8, 7.6), (-1.8, 7.6), (-2.5, 4.4)]
        pb = sb.wash(cr, body, core.mix("#4a3a2c", "#fff0b8", 0.85 * lantern_lit), 0.99, 0.2)
        sb.ink_outline(cr, pb, 0.4, "#2e2a28", 0.95)
        lamp = cr.user_to_device(0.0, 5.0)
        cr.restore()
    cr.restore()
    if alpha < 0.999:
        cr.pop_group_to_source()
        cr.paint_with_alpha(alpha)
    return lamp


# ----------------------------------------------------------------------------------------
# the illustrations
# ----------------------------------------------------------------------------------------

class _Synced(sb.Illustration):
    """An Illustration whose life follows the scene's event times (ev: name -> local seconds)."""

    def __init__(self, ev=None, seed=0):
        super().__init__(seed=seed)
        self.ev = dict(ev or {})

    def e(self, name, default=1e9):
        return self.ev.get(name, default)


def _house_front(cr, x, y, w, h_ground, h_upper, roof_h, wall, roof, seed, jetty=4.0, shutters="#4e8a6c"):
    """A half-timbered storybook house front with its ground at y; returns its features:
    door rect, lower window rect, upper windows [rects], the gable apex, the jetty line."""
    rng = random.Random(seed)
    ground_top = y - h_ground
    up_top = ground_top - h_upper
    # ground storey: stone with a plaster wash
    gs = sb.wobble([(x, y), (x, ground_top), (x + w, ground_top), (x + w, y)], 0.4, seed)
    pg = sb.wash(cr, gs, core.mix(wall, P["stone"], 0.45), 0.97, 0.35, w=0.7)
    cr.save()
    pg.add(cr)
    cr.clip()
    blocks = []
    for r in range(int(h_ground / 6.0) + 1):
        yy = y - r * 6.0
        xx = x - (r % 2) * 5.0
        while xx < x + w:
            ww = rng.uniform(8.0, 13.0)
            blocks.append([(xx, yy), (xx, yy - 6.0)])
            xx += ww
        blocks.append([(x, yy), (x + w, yy)])
    B.detail_lines(cr, blocks, 0.3, INK, 0.22, taper=(1.0, 1.0, 1.0))
    cr.restore()
    sb.ink_outline(cr, pg, 0.6, INK, 0.75)
    # upper storey: jettied, plaster + timber frame
    us = sb.wobble([(x - jetty, ground_top), (x - jetty, up_top), (x + w + jetty, up_top), (x + w + jetty, ground_top)],
                   0.4, seed + 1)
    pu = sb.wash(cr, us, wall, 0.97, 0.35, w=0.7)
    beams = [[(x - jetty - 1.0, ground_top), (x + w + jetty + 1.0, ground_top)],
             [(x - jetty, up_top), (x + w + jetty, up_top)]]
    for k in range(5):
        bx = x - jetty + (w + 2 * jetty) * k / 4.0
        beams.append([(bx, up_top), (bx, ground_top)])
    beams.append([(x - jetty, ground_top), (x - jetty + (w + 2 * jetty) / 4.0, up_top)])
    beams.append([(x + w + jetty, ground_top), (x + w + jetty - (w + 2 * jetty) / 4.0, up_top)])
    for b_ in beams:
        sb.ink(cr, b_, 1.9, P["umber"], 0.95, (0.9, 1.0, 0.9))
    sb.ink_outline(cr, pu, 0.6, INK, 0.75)
    # the corbels under the jetty
    for cx_ in (x + 2.0, x + w - 2.0):
        sb.ink(cr, [(cx_, ground_top), (cx_, ground_top + 4.5)], 1.6, P["umber"], 0.9)
    # gable roof
    apex = (x + w * 0.5, up_top - roof_h)
    rf = sb.wobble([(x - jetty - 4.0, up_top + 1.0), apex, (x + w + jetty + 4.0, up_top + 1.0)], 0.5, seed + 3)
    pr = sb.wash(cr, rf, roof, 0.97, 0.5, w=0.8)
    sb.hatch(cr, pr, 0.55, 2.4, 0.32, INK, 0.25)
    cr.save()
    pr.add(cr)
    cr.clip()
    tiles = []
    for r in range(1, int(roof_h / 3.2)):
        yy = up_top - r * 3.2
        tiles.append([(x - jetty - 6.0, yy), (x + w + jetty + 6.0, yy)])
    B.detail_lines(cr, tiles, 0.3, INK, 0.3, taper=(1.0, 1.0, 1.0))
    cr.restore()
    sb.ink_outline(cr, pr, 0.75, INK, 0.85)
    # carved bargeboard trim
    sb.ink(cr, [(x - jetty - 3.0, up_top + 0.5), apex, (x + w + jetty + 3.0, up_top + 0.5)], 1.0, P["umber"], 0.8)
    # windows: two upper (with shutters, animated by the caller), one lower beside the door
    uw, uh = w * 0.2, h_upper * 0.52
    ups = [(x + w * 0.26 - uw * 0.5, up_top + h_upper * 0.22, uw, uh), (x + w * 0.74 - uw * 0.5, up_top + h_upper * 0.22, uw, uh)]
    dw, dh = w * 0.24, h_ground * 0.74
    door = (x + w * 0.62 - dw * 0.5, y - dh, dw, dh)
    lw_ = (x + w * 0.2 - w * 0.09, y - h_ground * 0.72, w * 0.18, h_ground * 0.36)
    return {"door": door, "low": lw_, "ups": ups, "apex": apex, "jetty": ground_top, "top": up_top, "x": x, "w": w,
            "y": y, "shutters": shutters}


def _dress_house(cr, hf, lit=(0.0, 0.0), low_lit=0.0, door=True, flowers=None, seed=0):
    """Static dressing for a _house_front: leaded upper windows (lamplit or dark) with their
    shutters folded open, the lower window with a sill (or a flower box), a shut oak door."""
    for k, rect in enumerate(hf["ups"]):
        x, y0, w, h = rect
        lit_window(cr, x, y0, w, h, lit[k % len(lit)], arch=False)
        draw_shutters(cr, rect, 0.0, hf["shutters"])
    lx, ly, lw_, lh = hf["low"]
    lit_window(cr, lx, ly, lw_, lh, low_lit, arch=True)
    sb.ink(cr, [(lx - 1.2, ly + lh + 0.5), (lx + lw_ + 1.2, ly + lh + 0.5)], 1.3, P["umber"], 0.95)
    if flowers:
        rng = random.Random(seed)
        box = [(lx - 1.5, ly + lh + 0.6), (lx + lw_ + 1.5, ly + lh + 0.6), (lx + lw_ + 1.0, ly + lh + 4.0), (lx - 1.0, ly + lh + 4.0)]
        sb.ink_outline(cr, sb.wash(cr, box, "#7a4d2c", 0.98, 0.3), 0.4, INK, 0.8)
        for q in range(6):
            fx_ = lx + lw_ * (q + 0.5) / 6.0
            cr.new_path()
            core.circle(cr, fx_, ly + lh - 0.6 + rng.uniform(-0.8, 0.8), 1.2)
            core.src(cr, flowers[q % len(flowers)], 0.95)
            cr.fill()
    if door:
        draw_door(cr, hf["door"], open_=0.0, heart=1.0)


def _door_arch(dx, dy, dw, dh, n=8):
    pts = [(dx, dy + dh), (dx, dy + dw * 0.5)]
    for k in range(1, n):
        a = math.pi + math.pi * k / n
        pts.append((dx + dw * 0.5 + math.cos(a) * dw * 0.5, dy + dw * 0.5 + math.sin(a) * dw * 0.5))
    pts += [(dx + dw, dy + dw * 0.5), (dx + dw, dy + dh)]
    return pts


def heart_pts(cx, cy, r, n=28):
    out = []
    for k in range(n):
        a = TAU * k / n
        x_ = 16 * math.sin(a) ** 3
        y_ = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        out.append((cx + x_ * r / 16.0, cy + y_ * r / 16.0))
    return out


def draw_door(cr, rect, open_=0.0, slam=-1.0, t=0.0, heart=0.0, heart_glint=0.0, wood="#7a4d2c", interior=None):
    """An arched oak door with iron straps and a HEART-SHAPED iron lock plate.
    open_ 0 shut .. 1 wide (the dark interior shows); slam = seconds since it slammed (<0: not yet):
    a little shake; heart 0..1 the lock's bolt shot home (the plate goes dark iron, the keyhole
    closes); heart_glint 0..1 a gold glint on the plate."""
    dx, dy, dw, dh = rect
    arch = _door_arch(dx, dy, dw, dh)
    sb.wash(cr, arch, interior or "#1a120c", 0.98, 0.15)
    k = clamp(1.0 - open_)
    shake = 0.0
    if slam >= 0.0:
        shake = math.exp(-slam / 0.09) * math.sin(slam * 70.0) * 0.6
    if k > 0.02:
        cr.save()
        cr.new_path()
        core.polygon(cr, arch)
        cr.clip()
        cr.translate(dx, 0.0)
        cr.scale(k, 1.0)
        cr.translate(-dx + shake, 0.0)
        leaf = [(dx, dy - 2.0), (dx + dw, dy - 2.0), (dx + dw, dy + dh), (dx, dy + dh)]
        sb.wash(cr, leaf, wood, 0.99, 0.4, w=0.6)
        planks = [[(dx + dw * j / 4.0, dy), (dx + dw * j / 4.0, dy + dh)] for j in (1, 2, 3)]
        B.detail_lines(cr, planks, 0.35, INK, 0.5, taper=(1.0, 1.0, 1.0))
        straps = []
        for hy in (dy + dh * 0.32, dy + dh * 0.78):
            straps.append([(dx + 0.4, hy), (dx + dw * 0.7, hy)])
        B.detail_lines(cr, straps, 1.0, "#2b2522", 0.95, taper=(1.0, 1.0, 1.0))
        # the heart lock plate on the latch side
        hx, hy = dx + dw * 0.78, dy + dh * 0.55
        r = dw * 0.17
        hp = heart_pts(hx, hy, r)
        iron = core.mix("#6e6862", "#2e2926", heart)
        ph = sb.wash(cr, hp, iron, 0.99, 0.3)
        sb.ink_outline(cr, ph, 0.35, INK, 0.9)
        if heart < 0.95:
            cr.new_path()
            core.circle(cr, hx, hy - r * 0.1, r * 0.22 * (1.0 - heart))
            core.src(cr, "#120c08")
            cr.fill()
        # the bolt shooting home across the plate
        bx = lerp(hx - r * 2.2, hx - r * 0.2, heart)
        sb.ink(cr, [(bx - r * 1.4, hy + r * 0.9), (bx, hy + r * 0.9)], max(0.5, r * 0.32), "#3a3633", 1.0)
        if heart_glint > 0.01:
            fx.sparkle(cr, hx - r * 0.3, hy - r * 0.35, r * 1.6 * (0.6 + 0.4 * heart_glint), P["gold_hi"],
                       0.95 * heart_glint, angle=0.4)
        cr.restore()
    sb.ink_outline(cr, _poly(cr, arch), 0.75, INK, 0.9)


def draw_shutters(cr, rect, close=0.0, color="#4e8a6c", glow=0.0, latch_glint=0.0):
    """A pair of wooden shutters on a window: close 0 folded open beside it .. 1 shut over it
    (they swing on their hinges: a leaf is edge-on half way). glow: lamplight leaking between
    the slats when shut."""
    x, y, w, h = rect
    for side in (-1, 1):
        u = clamp(close)
        a = math.pi * (1.0 - u)               # pi = folded open flat against the wall, 0 = shut
        hinge = x if side < 0 else x + w
        half = w * 0.5
        span = half * math.cos(a)             # signed extent toward the window centre
        x0, x1 = hinge, hinge - side * span
        if abs(x1 - x0) < 0.2:
            sb.ink(cr, [(hinge, y), (hinge, y + h)], 0.8, core.shade(color, 0.4), 1.0)
            continue
        lo, hi = min(x0, x1), max(x0, x1)
        face_out = math.cos(a) < 0            # open: we see its painted outside face
        c = color if face_out or u > 0.5 else core.shade(color, 0.3)
        leaf = [(lo, y - 0.6), (hi, y - 0.6), (hi, y + h + 0.6), (lo, y + h + 0.6)]
        pl = sb.wash(cr, leaf, c, 0.99, 0.35, w=0.5)
        slats = [[(lo + 0.4, y + h * k / 5.0), (hi - 0.4, y + h * k / 5.0)] for k in range(1, 5)]
        B.detail_lines(cr, slats, 0.3, INK, 0.45, taper=(1.0, 1.0, 1.0))
        sb.ink_outline(cr, pl, 0.45, INK, 0.85)
    if close > 0.97:
        # the latch bar across the middle and a thread of light between the leaves
        if glow > 0.01:
            sb.ink(cr, [(x + w * 0.5, y + 0.5), (x + w * 0.5, y + h - 0.5)], 0.6, "#ffd27a", 0.9 * glow)
        sb.ink(cr, [(x + w * 0.22, y + h * 0.5), (x + w * 0.78, y + h * 0.5)], 0.9, "#2e2926", 1.0)
        if latch_glint > 0.01:
            fx.sparkle(cr, x + w * 0.55, y + h * 0.5, w * 0.28, P["gold_hi"], 0.85 * latch_glint)


# ----------------------------------------------------------------------------------------
# the town of shut doors: characterful house fronts (each one different), iron heart padlocks
# that click shut on "lock", latch bars that drop across the shutters on "latch"
# ----------------------------------------------------------------------------------------

def seg_ink(cr, pts, w, color=INK, alpha=0.9):
    """Ink a polyline with SHARP corners (each segment its own straight stroke): gable edges,
    bargeboards, hinges. sb.ink smooths through its points, which bulges a roof's apex."""
    B.detail_lines(cr, [[pts[i], pts[i + 1]] for i in range(len(pts) - 1)], w, color, alpha, taper=(1.0, 1.0, 1.0))


def scallop_rows(cr, x0, x1, y0, y1, row_h, cell_w, color, alpha, w=0.32, stagger=True):
    """Fish-scale tiles / shingles (an illuminator's pattern): rows of little arcs between y0 and y1
    (call inside a clip)."""
    arcs = []
    y = y1
    r = 0
    while y > y0 - row_h:
        x = x0 - (cell_w * 0.5 if (stagger and r % 2) else 0.0)
        while x < x1 + cell_w:
            arcs.append([(x, y - row_h * 0.15), (x + cell_w * 0.5, y + row_h * 0.62), (x + cell_w, y - row_h * 0.15)])
            x += cell_w
        y -= row_h
        r += 1
    B.detail_lines(cr, arcs, w, color, alpha, taper=(0.5, 1.0, 0.5))


def _stone_courses(cr, x0, x1, y_bot, y_top, rng, course=6.0, w=0.3, alpha=0.22):
    rows = []
    r = 0
    y = y_bot
    while y > y_top:
        xx = x0 - (r % 2) * 5.0
        while xx < x1:
            rows.append([(xx, y), (xx, y - course)])
            xx += rng.uniform(8.0, 13.0)
        rows.append([(x0, y), (x1, y)])
        y -= course
        r += 1
    B.detail_lines(cr, rows, w, INK, alpha, taper=(1.0, 1.0, 1.0))


def town_house(cr, x, y, w, hg, hu, roof_h, wall, roof_c, shutters, seed, roof="gable", jetty=3.5,
               door_u=0.62, low_u=0.2, ups_u=(0.26, 0.74), timber="x", chimney=None, sign=None, dormer=False,
               stone=None, door_w=0.26, door_h=0.78):
    """A storybook half-timbered house front standing on y (its doorstep line), seen face on:
    a coursed-stone ground storey, a jettied timber-framed upper storey (timber = "x" braces,
    "close" studding or "arch" braces), and a roof ("gable" with fish-scale tiles, "hip" with a
    dormer, or "thatch"). Returns its features (door, lower window, upper windows, eaves...)."""
    rng = random.Random(seed)
    gtop = y - hg
    utop = gtop - hu
    stone = stone or core.mix(wall, P["stone"], 0.5)
    # --- ground storey: coursed stone under a lime wash
    gs = sb.wobble([(x, y), (x, gtop), (x + w, gtop), (x + w, y)], 0.35, seed)
    pg = sb.wash(cr, gs, stone, 0.98, 0.35, w=0.7)
    cr.save()
    pg.add(cr)
    cr.clip()
    _stone_courses(cr, x - 2, x + w + 2, y, gtop, rng)
    # the jetty's shadow on the ground storey, and a darker foot
    cr.set_source(core.linear(0, gtop, 0, gtop + 9.0, [(0.0, (0.12, 0.08, 0.14, 0.42)), (1.0, (0.12, 0.08, 0.14, 0.0))]))
    cr.rectangle(x - 2, gtop, w + 4, 9.0)
    cr.fill()
    cr.set_source(core.linear(0, y - 6.0, 0, y, [(0.0, (0.1, 0.07, 0.06, 0.0)), (1.0, (0.1, 0.07, 0.06, 0.22))]))
    cr.rectangle(x - 2, y - 6.0, w + 4, 6.0)
    cr.fill()
    cr.restore()
    sb.ink_outline(cr, pg, 0.6, INK, 0.75)
    # --- upper storey: jettied, lime plaster + oak frame
    xl, xr = x - jetty, x + w + jetty
    us = sb.wobble([(xl, gtop), (xl, utop), (xr, utop), (xr, gtop)], 0.35, seed + 1)
    pu = sb.wash(cr, us, wall, 0.98, 0.35, w=0.7)
    cr.save()
    pu.add(cr)
    cr.clip()
    # the eaves' shadow along the top of the wall
    cr.set_source(core.linear(0, utop, 0, utop + 7.0, [(0.0, (0.12, 0.08, 0.14, 0.38)), (1.0, (0.12, 0.08, 0.14, 0.0))]))
    cr.rectangle(xl, utop, xr - xl, 7.0)
    cr.fill()
    cr.restore()
    oak = core.mix(P["umber"], "#3a2416", 0.25)
    beams = [[(xl - 0.8, gtop), (xr + 0.8, gtop)], [(xl, utop + 0.6), (xr, utop + 0.6)]]
    nposts = 4
    posts = [xl + (xr - xl) * k / nposts for k in range(nposts + 1)]
    for px_ in posts:
        beams.append([(px_, utop), (px_, gtop)])
    braces = []
    if timber == "x":
        for k in (0, nposts - 1):
            a_, b_ = posts[k], posts[k + 1]
            braces += [[(a_, gtop), (b_, utop)], [(b_, gtop), (a_, utop)]]
    elif timber == "close":
        k = xl + 2.6
        while k < xr - 1.0:
            braces.append([(k, utop + 1.0), (k, gtop - 1.0)])
            k += 3.2
        beams.append([(xl, (utop + gtop) * 0.5), (xr, (utop + gtop) * 0.5)])
    else:   # "arch": curved braces springing from the posts
        for k in (0, nposts - 1):
            a_, b_ = posts[k], posts[k + 1]
            m_ = (a_ + b_) * 0.5
            braces.append([(a_, gtop - 1.0), (a_ + (m_ - a_) * 0.35, utop + hu * 0.45), (m_, utop + 1.2)])
            braces.append([(b_, gtop - 1.0), (b_ - (b_ - m_) * 0.35, utop + hu * 0.45), (m_, utop + 1.2)])
    B.detail_lines(cr, braces, 1.25, oak, 0.92, taper=(0.9, 1.0, 0.9))
    B.detail_lines(cr, beams, 1.8, oak, 0.95, taper=(1.0, 1.0, 1.0))
    sb.ink_outline(cr, pu, 0.6, INK, 0.75)
    # corbels under the jetty
    for cx_ in (x + 1.8, x + w - 1.8):
        seg_ink(cr, [(cx_, gtop), (cx_, gtop + 4.2), (cx_ + (1.8 if cx_ < x + w / 2 else -1.8), gtop + 0.4)], 1.1, oak, 0.9)
    # --- the roof
    ov = 4.5
    rl, rr = xl - ov, xr + ov
    apex = (x + w * 0.5, utop - roof_h)
    feat = {}
    if roof == "thatch":
        cap_pts = [(rl - 1.0, utop + 2.0)]
        for k in range(1, 12):
            u = k / 12.0
            a = math.pi * (1.0 - u)
            cap_pts.append((x + w * 0.5 + math.cos(a) * (rr - rl) * 0.5, utop - math.sin(a) * roof_h * 1.05 + 1.0))
        cap_pts.append((rr + 1.0, utop + 2.0))
        pr = sb.wash(cr, cap_pts, roof_c, 0.98, 0.45, smooth_t=0.55, w=0.8)
        cr.save()
        pr.add(cr)
        cr.clip()
        straw = []
        for k in range(46):
            sx_ = rl + (rr - rl) * rng.random()
            sy_ = utop - rng.random() * roof_h
            straw.append([(sx_, sy_), (sx_ + rng.uniform(-0.6, 0.6), sy_ + rng.uniform(2.5, 4.5))])
        B.detail_lines(cr, straw, 0.35, core.shade(roof_c, 0.45), 0.55)
        # the ridge's woven band and a scalloped eave edge
        cr.set_source(core.linear(0, utop - roof_h, 0, utop + 2, [(0.0, (1, 0.95, 0.8, 0.18)), (0.5, (1, 1, 1, 0.0)),
                                                                   (1.0, (0.2, 0.1, 0.05, 0.35))]))
        cr.paint()
        cr.restore()
        sb.ink_outline(cr, pr, 0.75, INK, 0.85)
        eave = []
        k = rl
        while k < rr:
            eave.append([(k, utop + 1.6), (k + 1.6, utop + 3.4), (k + 3.2, utop + 1.6)])
            k += 3.2
        B.detail_lines(cr, eave, 0.45, core.shade(roof_c, 0.55), 0.8)
        feat["ridge"] = (x + w * 0.5, utop - roof_h)
    elif roof == "hip":
        top_w = w * 0.42
        poly = [(rl, utop + 1.0), (x + w * 0.5 - top_w * 0.5, utop - roof_h), (x + w * 0.5 + top_w * 0.5, utop - roof_h),
                (rr, utop + 1.0)]
        pr = sb.wash(cr, poly, roof_c, 0.98, 0.45, w=0.8)
        cr.save()
        pr.add(cr)
        cr.clip()
        scallop_rows(cr, rl, rr, utop - roof_h, utop, 3.0, 3.6, core.shade(roof_c, 0.5), 0.55)
        cr.set_source(core.linear(0, utop - roof_h, 0, utop, [(0.0, (1, 0.95, 0.85, 0.16)), (1.0, (0.2, 0.08, 0.06, 0.25))]))
        cr.paint()
        cr.restore()
        sb.ink_outline(cr, pr, 0.75, INK, 0.85)
        seg_ink(cr, [(rl - 0.5, utop + 1.2), poly[1], poly[2], (rr + 0.5, utop + 1.2)], 0.9, oak, 0.9)
        feat["ridge"] = (x + w * 0.5, utop - roof_h)
        if dormer:
            dx_, dw_ = x + w * 0.5, 9.0
            dy_ = utop - roof_h * 0.42
            dp = [(dx_ - dw_ * 0.5, dy_ + 6.0), (dx_ - dw_ * 0.5, dy_), (dx_, dy_ - 5.0), (dx_ + dw_ * 0.5, dy_),
                  (dx_ + dw_ * 0.5, dy_ + 6.0)]
            sb.ink_outline(cr, sb.wash(cr, dp, wall, 0.99, 0.3), 0.55, INK, 0.85)
            seg_ink(cr, [(dx_ - dw_ * 0.5 - 1.2, dy_ + 0.6), (dx_, dy_ - 5.6), (dx_ + dw_ * 0.5 + 1.2, dy_ + 0.6)], 1.0,
                    core.shade(roof_c, 0.3), 0.95)
            feat["dormer"] = (dx_ - 2.4, dy_ + 0.4, 4.8, 4.6)
    else:   # gable: steep, fish-scale tiles, carved bargeboards with a gilt finial
        poly = [(rl, utop + 1.0), apex, (rr, utop + 1.0)]
        pr = sb.wash(cr, poly, roof_c, 0.98, 0.45, w=0.8)
        cr.save()
        pr.add(cr)
        cr.clip()
        scallop_rows(cr, rl, rr, apex[1], utop, 3.0, 3.6, core.shade(roof_c, 0.5), 0.55)
        cr.set_source(core.linear(rl, 0, rr, 0, [(0.0, (1, 0.95, 0.85, 0.14)), (0.5, (1, 1, 1, 0.0)),
                                                  (1.0, (0.15, 0.06, 0.08, 0.28))]))
        cr.paint()
        cr.restore()
        sb.ink_outline(cr, pr, 0.75, INK, 0.85)
        seg_ink(cr, [(rl - 0.5, utop + 1.4), (apex[0], apex[1] - 0.6), (rr + 0.5, utop + 1.4)], 1.3, oak, 0.95)
        gold_star(cr, apex[0], apex[1] - 2.2, 1.9, points=4, inner=0.35)
        feat["ridge"] = apex
    # --- the chimney (smoke is drawn per frame from feat["chimney"])
    if chimney is not None:
        cx_, ch_h = chimney
        rf_y = utop - roof_h * 0.55
        stack = [(cx_ - 3.2, rf_y + 6.0), (cx_ - 3.2, rf_y - ch_h), (cx_ + 3.2, rf_y - ch_h), (cx_ + 3.2, rf_y + 6.0)]
        ps = sb.wash(cr, stack, "#8a5a4a", 0.99, 0.3)
        cr.save()
        ps.add(cr)
        cr.clip()
        _stone_courses(cr, cx_ - 4, cx_ + 4, rf_y + 6.0, rf_y - ch_h, rng, course=2.4, w=0.22, alpha=0.3)
        cr.restore()
        sb.ink_outline(cr, ps, 0.5, INK, 0.85)
        sb.ink_outline(cr, sb.wash(cr, [(cx_ - 4.2, rf_y - ch_h), (cx_ + 4.2, rf_y - ch_h), (cx_ + 4.2, rf_y - ch_h - 1.8),
                                        (cx_ - 4.2, rf_y - ch_h - 1.8)], "#6a4438", 0.99, 0.2), 0.45, INK, 0.85)
        feat["chimney"] = (cx_, rf_y - ch_h - 2.0)
    # --- openings
    uw, uh = w * 0.19, hu * 0.54
    ups = [(x + w * u_ - uw * 0.5, utop + hu * 0.2, uw, uh) for u_ in ups_u]
    dw, dh = w * door_w, hg * door_h
    door = (x + w * door_u - dw * 0.5, y - dh, dw, dh)
    lw_ = (x + w * low_u - w * 0.09, y - hg * 0.74, w * 0.18, hg * 0.36)
    # a deep stone reveal round the door, a worn step
    dx, dy, dw_, dh_ = door
    sb.ink_outline(cr, sb.wash(cr, _door_arch(dx - 1.8, dy - 1.8, dw_ + 3.6, dh_ + 1.8), core.shade(stone, 0.25), 0.98, 0.25),
                   0.5, INK, 0.8)
    sb.wash(cr, [(dx - 3.0, y), (dx + dw_ + 3.0, y), (dx + dw_ + 4.0, y + 2.4), (dx - 4.0, y + 2.4)], "#86807a", 0.98, 0.3)
    feat.update({"door": door, "low": lw_, "ups": ups, "apex": apex, "jetty": gtop, "top": utop, "x": x, "w": w, "y": y,
                 "shutters": shutters, "xl": xl, "xr": xr, "wall": wall})
    return feat


def draw_heart_padlock(cr, x, y, r, shut=0.0, swing=0.0, glint=0.0, t=0.0, open_side=1.0):
    """An iron HEART-SHAPED padlock hanging from the hasp staple at (x, y) (r = the heart's half
    width). shut 0: the shackle stands open (one leg out of the body, the lock hanging slack at an
    angle) .. 1: snapped shut; swing (rad) rocks it on the staple; glint 0..1 runs a burnished
    highlight over its face (light catching iron -- not a magic sparkle)."""
    cr.save()
    cr.translate(x, y)
    cr.rotate(swing + 0.32 * (1.0 - shut) * open_side)
    # the shackle: a thick iron U through the staple; open = lifted and swung aside on one leg
    lift = 0.55 * r * (1.0 - shut)
    sw = r * 0.62
    top = -0.15 * r - lift
    leg = r * 1.25
    cr.save()
    cr.translate(open_side * sw * (1.0 - shut) * 0.55, 0.0)
    pts = [(-sw, top + leg), (-sw, top + r * 0.2)]
    for k in range(1, 9):
        a = math.pi + math.pi * k / 9
        pts.append((math.cos(a) * sw, top + r * 0.2 + math.sin(a) * sw))
    pts += [(sw, top + r * 0.2), (sw, top + leg * (0.55 + 0.45 * shut))]
    B.detail_line(cr, pts, r * 0.26, "#2a2624", 1.0, taper=(1.0, 1.0, 1.0))
    B.detail_line(cr, pts[1:-1], r * 0.09, "#8a8480", 0.7, taper=(0.3, 1.0, 0.3))
    cr.restore()
    # the heart-shaped body (iron, with a pewter bevel and a keyhole)
    by_ = top + leg * 0.92 + r * 0.95
    hp = heart_pts(0.0, by_, r * 1.02)
    ph = sb.wash(cr, hp, "#4c4744", 0.99, 0.0)
    cr.save()
    ph.add(cr)
    cr.clip()
    g = core.linear(-r, by_ - r, r, by_ + r, [(0.0, "#8d8781"), (0.45, "#4f4946"), (1.0, "#2a2523")])
    cr.set_source(g)
    cr.paint()
    inner = heart_pts(0.0, by_ + r * 0.06, r * 0.74)
    cr.new_path()
    core.polygon(cr, inner)
    core.src(cr, "#3c3734", 0.85)
    cr.fill()
    if glint > 0.01:
        # a burnished sweep across the face (candle-gold on iron)
        gx = lerp(-1.6 * r, 1.6 * r, glint)
        sg = core.linear(gx - r * 0.5, by_ - r, gx + r * 0.5, by_ + r,
                         [(0.0, (1.0, 0.85, 0.5, 0.0)), (0.5, (1.0, 0.9, 0.62, 0.8 * math.sin(math.pi * glint))),
                          (1.0, (1.0, 0.85, 0.5, 0.0))])
        cr.set_source(sg)
        cr.paint()
    cr.restore()
    sb.ink_outline(cr, ph, max(0.3, r * 0.1), "#1c1816", 0.95)
    # keyhole + rivets
    cr.new_path()
    core.circle(cr, 0.0, by_ - r * 0.12, r * 0.17)
    cr.move_to(-r * 0.09, by_ - r * 0.08)
    cr.line_to(r * 0.09, by_ - r * 0.08)
    cr.line_to(r * 0.14, by_ + r * 0.4)
    cr.line_to(-r * 0.14, by_ + r * 0.4)
    cr.close_path()
    core.src(cr, "#120d0b")
    cr.fill()
    for (rx_, ry_) in ((-r * 0.55, by_ - r * 0.45), (r * 0.55, by_ - r * 0.45)):
        cr.new_path()
        core.circle(cr, rx_, ry_, r * 0.08)
        core.src(cr, "#a8a29a", 0.8)
        cr.fill()
    cr.restore()


def draw_town_door(cr, rect, open_=0.0, slam=-1.0, t=0.0, lock=0.0, swing=0.0, glint=0.0, wood="#7a4d2c",
                   interior=None, lamp=0.0):
    """An arched oak door with scrolled iron strap hinges, a ring pull and the HEART PADLOCK on its
    hasp. open_ 0 shut .. 1 wide (the lamplit hall shows: lamp 0..1); slam = s since it slammed
    (a shake); lock 0..1 the padlock's shackle snaps shut; swing its rock; glint its burnish."""
    dx, dy, dw, dh = rect
    arch = _door_arch(dx, dy, dw, dh)
    inside = interior or core.mix("#1a120c", "#ffb24a", 0.55 * lamp)
    sb.wash(cr, arch, inside, 0.99, 0.15)
    if lamp > 0.02:
        soft_glow(cr, dx + dw * 0.5, dy + dh * 0.7, dw * 0.9, "#ffcf7a", 0.5 * lamp)
    k = clamp(1.0 - open_)
    shake = 0.0
    if slam >= 0.0:
        shake = math.exp(-slam / 0.09) * math.sin(slam * 70.0) * 0.6
    if k > 0.02:
        cr.save()
        cr.new_path()
        core.polygon(cr, arch)
        cr.clip()
        cr.translate(dx, 0.0)
        cr.scale(k, 1.0)
        cr.translate(-dx + shake, 0.0)
        leaf = [(dx, dy - 2.0), (dx + dw, dy - 2.0), (dx + dw, dy + dh), (dx, dy + dh)]
        sb.wash(cr, leaf, wood, 0.99, 0.4, w=0.6)
        planks = [[(dx + dw * j / 4.0, dy), (dx + dw * j / 4.0, dy + dh)] for j in (1, 2, 3)]
        B.detail_lines(cr, planks, 0.35, INK, 0.5, taper=(1.0, 1.0, 1.0))
        # the arch's shadow at the top of the leaf
        cr.set_source(core.linear(0, dy, 0, dy + dw * 0.7, [(0.0, (0.1, 0.05, 0.03, 0.35)), (1.0, (0.1, 0.05, 0.03, 0.0))]))
        cr.rectangle(dx, dy - 2, dw, dw * 0.7 + 2)
        cr.fill()
        # strap hinges ending in Kells scrolls
        for hy in (dy + dh * 0.3, dy + dh * 0.8):
            B.detail_line(cr, [(dx + 0.2, hy), (dx + dw * 0.62, hy)], 1.05, "#2b2522", 0.95, taper=(1.0, 1.0, 0.7))
            sp = spiral_pts(dx + dw * 0.62 + 1.1, hy - 0.2, 0.2, 1.3, turns=1.1, n=10, a0=math.pi, cw=-1)
            B.detail_line(cr, sp, 0.55, "#2b2522", 0.95, taper=(0.6, 1.0, 0.4))
        # the ring pull
        rx_, ry_ = dx + dw * 0.3, dy + dh * 0.56
        cr.new_path()
        cr.arc(rx_, ry_ + 1.2, 1.25, 0, TAU)
        cr.set_line_width(0.45)
        core.src(cr, "#2b2522", 0.95)
        cr.stroke()
        # the hasp: a hinged iron strap from the jamb over a staple
        hx_, hy_ = dx + dw * 0.8, dy + dh * 0.47
        B.detail_line(cr, [(dx + dw + 0.6, hy_ - 0.9), (hx_ - 1.6, hy_ - 0.9)], 1.0, "#2b2522", 0.95, taper=(1.0, 1.0, 1.0))
        cr.new_path()
        core.circle(cr, hx_, hy_, 0.85)
        cr.set_line_width(0.45)
        core.src(cr, "#2b2522", 0.95)
        cr.stroke()
        draw_heart_padlock(cr, hx_, hy_ + 0.4, dw * 0.21, shut=lock, swing=swing, glint=glint, t=t)
        cr.restore()
    sb.ink_outline(cr, _poly(cr, arch), 0.75, INK, 0.9)


def draw_town_shutters(cr, rect, close=0.0, color="#4e8a6c", glow=0.0, latch=0.0, t=0.0):
    """A pair of slatted shutters on a window: close 0 folded open beside it .. 1 swung shut over it
    (a leaf is edge-on halfway); then the iron LATCH BAR drops across both leaves (latch 0..1: it
    swings down from upright on its pivot, overshoots and settles in its keeper). glow: lamplight
    leaking between the leaves once shut."""
    x, y, w, h = rect
    for side in (-1, 1):
        u = clamp(close)
        a = math.pi * (1.0 - u)
        hinge = x if side < 0 else x + w
        half = w * 0.5
        span = half * math.cos(a)
        x0, x1 = hinge, hinge - side * span
        if abs(x1 - x0) < 0.2:
            sb.ink(cr, [(hinge, y), (hinge, y + h)], 0.8, core.shade(color, 0.4), 1.0)
            continue
        lo, hi = min(x0, x1), max(x0, x1)
        face_out = math.cos(a) < 0
        c = color if face_out or u > 0.5 else core.shade(color, 0.3)
        leaf = [(lo, y - 0.6), (hi, y - 0.6), (hi, y + h + 0.6), (lo, y + h + 0.6)]
        pl = sb.wash(cr, leaf, c, 0.99, 0.35, w=0.5)
        slats = [[(lo + 0.4, y + h * k / 6.0), (hi - 0.4, y + h * k / 6.0)] for k in range(1, 6)]
        B.detail_lines(cr, slats, 0.28, INK, 0.45, taper=(1.0, 1.0, 1.0))
        sb.ink_outline(cr, pl, 0.45, INK, 0.85)
    if close > 0.97:
        if glow > 0.01:
            B.detail_line(cr, [(x + w * 0.5, y + 0.5), (x + w * 0.5, y + h - 0.5)], 0.55, "#ffd27a", 0.9 * glow,
                          taper=(0.3, 1.0, 0.3))
            soft_glow(cr, x + w * 0.5, y + h * 0.5, w * 0.6, "#ffcf7a", 0.18 * glow)
        # the keeper (a hook on the right leaf) and the bar on its pivot (left leaf)
        px_, py_ = x + w * 0.2, y + h * 0.5
        kx_ = x + w * 0.8
        cr.new_path()
        cr.arc(kx_, py_ + 0.2, 0.75, -0.2, math.pi + 0.2)
        cr.set_line_width(0.45)
        core.src(cr, "#2b2522", 0.95)
        cr.stroke()
        if latch > 0.0:
            # down from upright (-pi/2) to across (0): overshoot and settle (out_back)
            ang = -math.pi * 0.5 * (1.0 - core.out_back(clamp(latch)))
            L_ = w * 0.66
            ex, ey = px_ + math.cos(ang) * L_, py_ + math.sin(ang) * L_
            B.detail_line(cr, [(px_, py_), (ex, ey)], 0.95, "#2b2522", 1.0, taper=(1.0, 1.0, 0.8))
        else:
            B.detail_line(cr, [(px_, py_), (px_, py_ - w * 0.66)], 0.95, "#2b2522", 1.0, taper=(1.0, 1.0, 0.8))
        cr.new_path()
        core.circle(cr, px_, py_, 0.6)
        core.src(cr, "#55504c", 1.0)
        cr.fill()


def dress_town_house(cr, hf, lit=(0.0, 0.0), shut=(False, False), low_lit=0.0, door=True, flowers=None, seed=0):
    """Static dressing for a town_house front (verse 2's streets): upper windows lamplit with the
    shutters folded open, or shut and latched; the lower window with its sill (or a flower box);
    the door shut with its heart padlock locked."""
    for k, rect in enumerate(hf["ups"]):
        x, y0, w, h = rect
        lk = lit[k % len(lit)]
        if lk > 0.02 and not shut[k % len(shut)]:
            soft_glow(cr, x + w * 0.5, y0 + h * 0.55, w * 1.25, "#ffbf5a", 0.22 * lk)
        lit_window(cr, x, y0, w, h, 0.0 if shut[k % len(shut)] else lk, arch=False)
        if shut[k % len(shut)]:
            draw_town_shutters(cr, rect, 1.0, hf["shutters"], glow=0.7 * lk, latch=1.0)
        else:
            draw_town_shutters(cr, rect, 0.0, hf["shutters"])
    lx, ly, lw_, lh = hf["low"]
    lit_window(cr, lx, ly, lw_, lh, low_lit, arch=True)
    seg_ink(cr, [(lx - 1.4, ly + lh + 0.5), (lx + lw_ + 1.4, ly + lh + 0.5)], 1.4, P["umber"], 0.95)
    if flowers:
        rng = random.Random(seed)
        box = [(lx - 1.5, ly + lh + 0.6), (lx + lw_ + 1.5, ly + lh + 0.6), (lx + lw_ + 1.0, ly + lh + 4.0), (lx - 1.0, ly + lh + 4.0)]
        sb.ink_outline(cr, sb.wash(cr, box, "#7a4d2c", 0.98, 0.3), 0.4, INK, 0.8)
        for q in range(6):
            fx_ = lx + lw_ * (q + 0.5) / 6.0
            cr.new_path()
            core.circle(cr, fx_, ly + lh - 0.6 + rng.uniform(-0.8, 0.8), 1.2)
            core.src(cr, flowers[q % len(flowers)], 0.95)
            cr.fill()
    if door:
        draw_town_door(cr, hf["door"], lock=1.0)


def ink_clack(cr, x, y, r, u, alpha=0.85, n=5, a0=-2.6, a1=-0.5):
    """A little fan of ink impact strokes (a 'clack!' drawn by the illuminator) radiating from
    (x, y) as u goes 0 -> 1."""
    if not 0.0 < u < 1.0:
        return
    al = math.sin(math.pi * min(1.0, u * 1.8)) * (1.0 - u) * alpha
    strokes = []
    for j in range(n):
        a = lerp(a0, a1, j / max(1, n - 1))
        r0, r1 = r * (0.5 + 0.8 * u), r * (1.2 + 1.2 * u)
        strokes.append([(x + math.cos(a) * r0, y + math.sin(a) * r0), (x + math.cos(a) * r1, y + math.sin(a) * r1)])
    B.detail_lines(cr, strokes, max(0.25, r * 0.12), INK, al, taper=(0.4, 1.0, 0.2))


def town_lantern(cr, x, y, t, phase=0.0, scale=1.0, side=1, warm=True):
    """sb._lantern, but it can hang from a wall on either side: side +1 the bracket comes from the
    wall at the left, -1 from a wall on the right (mirrored); the lantern hangs at (x + side*9*scale, y)."""
    cr.save()
    cr.translate(x, y)
    cr.scale(side, 1.0)
    sb._lantern(cr, 9.0 * scale, 0.0, t, phase=phase, scale=scale, warm=warm)
    cr.restore()


class CastleTown(_Synced):
    """Verse 1's great picture (spread 0, right page): the kingdom of stone at dusk -- a grey castle
    on its hill under an indigo sky (gold-leaf moon and stars, Kells cloud-curls), the road winding
    down through spiral-leaved trees to a street of half-timbered houses at the foot. The camera
    tilts down it. Life, on the lyrics: pennants fly; the castle's windows light on "kingdom of
    stone"; folk walk the street alone (one turns away from another); a lone figure appears in each
    upper window on "living alone"; potions glint on the sills on "potions"; a yawn and ink z's on
    "sleeping"; charms swing on "charms"; painted rain on "rain"; the folk hurry home, doors slam and
    the heart-shaped locks shoot home on "lock" (glinting on "heart"); the shutters swing shut and
    latch, one after another, on "latch"."""
    DW, DH = 200.0, 287.0
    grain = 0.3
    STREET_Y = 268.0                  # the doorsteps (ground line of the house fronts)

    def back(self, cr):
        rng = random.Random(self.seed)
        # --- sky: indigo -> violet -> rose -> peach at the horizon, washed and bloomed
        sb._sky(cr, self.DW, self.DH, [(0.0, "#181c40"), (0.16, "#262a5c"), (0.32, "#433f7c"), (0.45, "#755b8c"),
                                       (0.55, "#b3748a"), (0.62, "#e09d84"), (0.68, "#eebd8e")],
                seed=self.seed + 1, blooms=9, bottom=200)
        # Kells cloud-curls: long violet bands ending in gilt-edged spirals
        for (cx, cy, L, s_) in ((40, 52, 70, 1.0), (150, 84, 64, -1.0), (70, 118, 80, 1.0), (176, 138, 50, -1.0)):
            band = []
            for i in range(9):
                u = i / 8.0
                band.append((cx - s_ * L * 0.5 + s_ * L * u, cy + 2.4 * math.sin(u * 5.0 + cx)))
            top = [(px, py - 3.2 - 1.4 * math.sin(i * 1.1)) for i, (px, py) in enumerate(band)]
            bot = [(px, py + 2.6) for (px, py) in band]
            sb.wash(cr, top + bot[::-1], "#c8a8c8", 0.32, 0.25, smooth_t=0.6, w=0.5)
            sp = spiral_pts(band[-1][0] + s_ * 2.0, band[-1][1] - 2.0, 0.6, 5.2, turns=1.4, n=18, a0=math.pi * 0.5,
                            cw=1 if s_ > 0 else -1)
            sb.ink(cr, sp, 0.9, P["gold_dk"], 0.75, (0.4, 1.0, 0.8))
            sb.ink(cr, top, 0.5, "#efe2f2", 0.35, (0.2, 1.0, 0.2))
        # the gold-leaf moon with a sleepy face
        mx, my, mr = 140.0, 52.0, 12.5
        sb.gild(cr, crescent_pts(mx, my, mr, 6.0, -3.2, mr * 0.86), outline=0.6, shimmer=0.5)
        sb.ink(cr, [(mx - 9.0, my - 2.0), (mx - 7.4, my - 1.0), (mx - 5.8, my - 1.6)], 0.6, P["gold_dk"], 0.9)  # closed eye
        sb.ink(cr, [(mx - 10.4, my + 4.0), (mx - 8.0, my + 4.6)], 0.5, P["gold_dk"], 0.8)                      # a smile
        self._moon = (mx, my, mr)
        # gilded eight-point stars + painted pin-pricks
        self._stars = [(22, 22, 3.2), (60, 14, 2.4), (98, 30, 2.0), (118, 12, 2.8), (186, 66, 2.2), (14, 92, 1.8),
                       (128, 60, 1.6), (40, 80, 1.5)]
        for (sx_, sy_, r) in self._stars:
            gold_star(cr, sx_, sy_, r, rot=rng.uniform(0, 0.4))
        stipple(cr, 0, 0, self.DW, 110, 40, "#fff6dc", 0.35, (0.2, 0.45), seed=self.seed + 4)
        # --- far hills: two hazy violet bands with hatching
        far = sb.wobble([(-10, 172), (16, 150), (40, 158), (64, 140), (86, 150), (118, 136), (150, 150), (176, 140),
                         (212, 156), (212, 210), (-10, 210)], 1.0, 3)
        pf = sb.wash(cr, far, "#7c78a6", 0.85, 0.35, smooth_t=0.6)
        sb.hatch(cr, pf, -0.5, 3.6, 0.35, "#4e4a78", 0.25)
        far2 = sb.wobble([(-10, 186), (30, 166), (70, 178), (130, 162), (180, 176), (212, 168), (212, 220), (-10, 220)], 1.0, 4)
        pf2 = sb.wash(cr, far2, "#6b7aa0", 0.9, 0.35, smooth_t=0.6)
        sb.hatch(cr, pf2, 0.6, 3.2, 0.35, "#46507a", 0.22)
        # --- the castle hill: a steep crown, patterned field strips, hatching on its shadow side
        hill = sb.wobble([(-10, 236), (-10, 214), (24, 196), (52, 168), (74, 132), (88, 110), (112, 108), (128, 126),
                          (150, 162), (178, 190), (212, 206), (212, 236)], 1.0, 5)
        ph = sb.wash(cr, hill, "#5d7b48", 0.97, 0.45, smooth_t=0.55)
        cr.save()
        ph.add(cr)
        cr.clip()
        for k, (a, b_, c_) in enumerate(((-20, 150, "#6f8c50"), (10, 175, "#7e9a58"), (40, 196, "#58733f"),
                                        (110, 150, "#6a874c"), (140, 178, "#4f6a3c"), (170, 200, "#759252"))):
            strip = [(a, b_), (a + 60, b_ - 26), (a + 74, b_ - 20), (a + 14, b_ + 8)]
            sb.wash(cr, strip, c_, 0.75, 0.2)
        # rows of little furrows / hedges along the contours
        rows = []
        for r in range(9):
            yy = 140 + r * 10
            rows.append([(0, yy + 12), (50, yy - 4), (100, yy - 2), (150, yy + 6), (200, yy + 16)])
        B.detail_lines(cr, rows, 0.35, "#3c5230", 0.35)
        stipple(cr, 0, 110, self.DW, 240, 160, "#2f4224", 0.35, (0.25, 0.55), seed=self.seed + 7)
        # shadow side (right): hatching
        shade = [(100, 108), (212, 196), (212, 240), (100, 240)]
        cr.new_path()
        core.polygon(cr, shade)
        sb.hatch(cr, B.Path(cr), 0.9, 2.6, 0.35, "#2c3d22", 0.28)
        cr.restore()
        sb.ink_outline(cr, ph, 0.7, INK, 0.8)
        # --- the road, winding from the castle gate down to the town
        road = [(100, 106), (112, 120), (92, 138), (78, 152), (104, 170), (126, 186), (110, 204), (96, 222)]
        sb.ink(cr, road, 6.0, "#c9a05c", 0.92, (0.5, 1.0, 1.4))
        sb.ink(cr, road, 0.6, P["umber"], 0.55, (0.5, 1.0, 1.4))
        stipple(cr, 70, 110, 132, 222, 50, P["umber"], 0.3, (0.2, 0.4), seed=self.seed + 9)
        # --- trees: Kells round trees with spiral leaf curls, and dark cypress spires
        for (tx, ty, r, c_) in ((22, 200, 11, "#4b6a3a"), (40, 186, 8, "#56763f"), (172, 176, 10, "#4b6a3a"),
                                (190, 196, 12, "#3f5c33"), (140, 150, 7, "#56763f"), (60, 162, 6.5, "#4b6a3a")):
            sb.ink(cr, [(tx, ty + r * 0.6), (tx, ty + r * 1.6)], 1.6, P["umber"], 0.95)
            cr.new_path()
            core.blob(cr, tx, ty, r, 0.12, 9, seed=int(tx * 7 + ty))
            pt = sb.wash(cr, None, c_, 0.97, 0.5, path=B.Path(cr))
            cr.save()
            pt.add(cr)
            cr.clip()
            core.src(cr, "#9fbf6a", 0.35)
            cr.new_path()
            core.circle(cr, tx - r * 0.35, ty - r * 0.35, r * 0.55)
            cr.fill()
            cr.restore()
            sb.ink(cr, spiral_pts(tx + r * 0.1, ty, 0.4, r * 0.62, turns=1.3, n=16, a0=0.3), 0.55, "#2c3d22", 0.75)
            sb.ink_outline(cr, pt, 0.6, INK, 0.8)
        for (tx, ty, h_) in ((76, 128, 16), (126, 126, 15), (148, 140, 12), (56, 146, 12)):
            cyp = [(tx, ty - h_), (tx + 3.2, ty - h_ * 0.4), (tx + 2.6, ty), (tx - 2.6, ty), (tx - 3.2, ty - h_ * 0.4)]
            pcy = sb.wash(cr, cyp, "#2e4a30", 0.97, 0.4, smooth_t=0.5)
            sb.ink_outline(cr, pcy, 0.5, INK, 0.8)
        # --- the castle (cold grey stone)
        self._draw_castle(cr)
        # --- the town street at the foot
        self._draw_town(cr, rng)

    def _draw_castle(self, cr):
        st = "#9aa0b2"
        st_dk = core.shade(P["slate"], 0.2)
        cx = 100.0
        base = 110.0
        towers = []

        def tower(tx, top, tw, roof_c, bottom=base):
            body = [(tx, bottom), (tx, top), (tx + tw, top), (tx + tw, bottom)]
            pb = sb.wash(cr, body, st, 0.98, 0.4)
            sb.wash(cr, [(tx + tw * 0.62, top), (tx + tw, top), (tx + tw, bottom), (tx + tw * 0.62, bottom)], st_dk, 0.45, 0.0)
            cr.save()
            pb.add(cr)
            cr.clip()
            courses = [[(tx, yy), (tx + tw, yy)] for yy in [top + 4.0 + 3.6 * k for k in range(int((bottom - top) / 3.6))]]
            B.detail_lines(cr, courses, 0.25, INK, 0.25, taper=(1.0, 1.0, 1.0))
            cr.restore()
            roof = [(tx - 2.2, top + 0.6), (tx + tw * 0.5, top - tw * 1.7), (tx + tw + 2.2, top + 0.6)]
            pr = sb.wash(cr, roof, roof_c, 0.98, 0.5)
            sb.hatch(cr, pr, 0.9, 1.8, 0.3, INK, 0.3)
            sb.ink_outline(cr, pr, 0.65, INK, 0.9)
            sb.ink_outline(cr, pb, 0.65, INK, 0.9)
            towers.append((tx + tw * 0.5, top - tw * 1.7))
            return pb

        # curtain wall with merlons
        wall = [(66, base), (66, 86), (134, 86), (134, base)]
        pw = sb.wash(cr, wall, st, 0.98, 0.4)
        cr.save()
        pw.add(cr)
        cr.clip()
        rows = []
        rng = random.Random(41)
        for r in range(7):
            yy = 86 + r * 3.6
            rows.append([(66, yy), (134, yy)])
            xx = 66 + (r % 2) * 2.5
            while xx < 134:
                rows.append([(xx, yy), (xx, yy + 3.6)])
                xx += rng.uniform(4.5, 7.0)
        B.detail_lines(cr, rows, 0.25, INK, 0.28, taper=(1.0, 1.0, 1.0))
        cr.restore()
        sb.ink_outline(cr, pw, 0.7, INK, 0.9)
        for k in range(12):
            mx_ = 67 + k * 5.8
            sb.wash(cr, [(mx_, 86.5), (mx_, 82.6), (mx_ + 3.2, 82.6), (mx_ + 3.2, 86.5)], st, 0.98, 0.25)
            sb.ink_outline(cr, _poly(cr, [(mx_, 86.5), (mx_, 82.6), (mx_ + 3.2, 82.6), (mx_ + 3.2, 86.5)]), 0.4, INK, 0.75)
        # the keep and its tall spire tower
        keep = [(86, 88), (86, 50), (114, 50), (114, 88)]
        pk = sb.wash(cr, keep, core.tint(st, 0.08), 0.98, 0.4)
        sb.wash(cr, [(104, 50), (114, 50), (114, 88), (104, 88)], st_dk, 0.4, 0.0)
        sb.hatch(cr, pk, 1.2, 2.2, 0.3, INK, 0.2)
        sb.ink_outline(cr, pk, 0.7, INK, 0.9)
        for k in range(6):
            mx_ = 86.6 + k * 4.8
            sb.wash(cr, [(mx_, 50.5), (mx_, 47.0), (mx_ + 2.8, 47.0), (mx_ + 2.8, 50.5)], core.tint(st, 0.08), 0.98, 0.25)
        tower(58, 72, 13, P["vermilion"])
        tower(129, 70, 13, P["vermilion"])
        tower(95, 26, 10, P["madder"], bottom=50)
        self._tips = towers
        # the gate with its portcullis
        gate = [(94, base), (94, 99)] + [(100 - math.cos(math.pi * k / 6) * 6, 99 - math.sin(math.pi * k / 6) * 6) for k in range(7)] + [(106, 99), (106, base)]
        pg = sb.wash(cr, gate, "#1e1712", 0.98, 0.2)
        cr.save()
        pg.add(cr)
        cr.clip()
        grid = [[(94 + i * 2.0, 90), (94 + i * 2.0, base)] for i in range(7)] + [[(94, 95 + j * 3.0), (106, 95 + j * 3.0)] for j in range(5)]
        B.detail_lines(cr, grid, 0.4, "#6a5a44", 0.8, taper=(1.0, 1.0, 1.0))
        cr.restore()
        sb.ink_outline(cr, pg, 0.6, INK, 0.9)
        # window slits (they light up on "kingdom of stone"): positions saved for anim
        self._cwin = [(62.0, 80.0), (133.0, 78.0), (91.0, 60.0), (100.0, 60.0), (109.0, 60.0), (98.6, 34.0),
                      (62.0, 92.0), (133.0, 92.0), (91.0, 72.0), (109.0, 72.0)]
        for (wx, wy) in self._cwin:
            sb.wash(cr, [(wx, wy), (wx + 2.6, wy), (wx + 2.6, wy + 5.0), (wx, wy + 5.0)], "#1c2040", 0.98, 0.0)

    def _draw_town(self, cr, rng):
        y = self.STREET_Y
        # the town wall at the hill's foot (behind everything in the street)
        tw = sb.wobble([(-10, 212), (212, 212), (212, 232), (-10, 232)], 0.5, 11)
        ptw = sb.wash(cr, tw, "#8b8ea0", 0.97, 0.35)
        merl = [[(x_, 212), (x_, 208.5), (x_ + 3.2, 208.5), (x_ + 3.2, 212)] for x_ in range(-8, 212, 6)]
        for m in merl:
            sb.wash(cr, m, "#8b8ea0", 0.97, 0.2)
        sb.ink_outline(cr, ptw, 0.5, INK, 0.7)
        # --- the back row: hazy gables between the wall and the street (depth), a few lamplit
        #     windows, chimneys (the smoke lives in anim)
        self._back_chimneys = []
        bx = -14.0
        brng = random.Random(self.seed + 31)
        haze = "#8f8aaa"
        while bx < 214.0:
            bw = brng.uniform(18.0, 30.0)
            bh = brng.uniform(16.0, 30.0)
            rh = brng.uniform(9.0, 16.0)
            base = 236.0
            body = [(bx, base), (bx, base - bh), (bx + bw * 0.5, base - bh - rh), (bx + bw, base - bh), (bx + bw, base)]
            col = core.mix(haze, "#6f6a92", brng.uniform(0.0, 0.5))
            pb = sb.wash(cr, body, col, 0.96, 0.25)
            cr.save()
            pb.add(cr)
            cr.clip()
            cr.set_source(core.linear(0, base - bh - rh, 0, base, [(0.0, (0.95, 0.8, 0.75, 0.12)), (1.0, (0.15, 0.12, 0.25, 0.35))]))
            cr.paint()
            cr.restore()
            seg_ink(cr, [(bx - 1.0, base - bh + 0.6), (bx + bw * 0.5, base - bh - rh), (bx + bw + 1.0, base - bh + 0.6)], 0.7,
                    "#4e4870", 0.8)
            if brng.random() < 0.6:
                wx_, wy_ = bx + bw * brng.uniform(0.3, 0.6), base - bh * brng.uniform(0.45, 0.75)
                sb.wash(cr, [(wx_, wy_), (wx_ + 2.6, wy_), (wx_ + 2.6, wy_ + 3.4), (wx_, wy_ + 3.4)], "#ffcf7a", 0.9, 0.0)
                soft_glow(cr, wx_ + 1.3, wy_ + 1.7, 5.0, "#ffbf5a", 0.18)
            if brng.random() < 0.45:
                cx_ = bx + bw * brng.uniform(0.62, 0.8)
                cy_ = base - bh - rh * 0.5
                sb.wash(cr, [(cx_ - 1.6, cy_ + 2), (cx_ - 1.6, cy_ - 6), (cx_ + 1.6, cy_ - 6), (cx_ + 1.6, cy_ + 2)], "#6c5a6e", 0.96, 0.1)
                self._back_chimneys.append((cx_, cy_ - 6.5))
            bx += bw + brng.uniform(-4.0, 1.0)
        # a soft evening haze over the back row (atmospheric depth)
        cr.set_source(core.linear(0, 190, 0, 240, [(0.0, (0.85, 0.72, 0.78, 0.0)), (1.0, (0.85, 0.72, 0.78, 0.22))]))
        cr.rectangle(-10, 190, 220, 50)
        cr.fill()
        # --- the alleys between the houses: deep plum shadow with a far lamp at the end
        for ax in (57.0, 126.0):
            al = [(ax, y + 1.0), (ax, 214.0), (ax + 17.0, 214.0), (ax + 17.0, y + 1.0)]
            pa = sb.wash(cr, al, "#2e2440", 0.98, 0.2)
            cr.save()
            pa.add(cr)
            cr.clip()
            soft_glow(cr, ax + 7.0, 246.0, 7.0, "#ffb24a", 0.35)
            cr.restore()
        # --- the cobbled street: fish-scale setts, a gutter down the middle, darker near the walls
        street = [(-6, y - 2.0), (206, y - 2.0), (206, self.DH + 4), (-6, self.DH + 4)]
        ps = sb.wash(cr, street, "#9a938a", 0.97, 0.3)
        cr.save()
        ps.add(cr)
        cr.clip()
        arcs = []
        yy = y + 1.0
        row = 0
        while yy < self.DH + 4:
            xx = -8.0 - (row % 2) * 4.0
            ww_ = 6.5 + row * 0.9
            while xx < 210:
                w_ = rng.uniform(ww_ * 0.85, ww_ * 1.2)
                arcs.append([(xx + 0.8, yy + 1.8 + row * 0.3), (xx + w_ * 0.5, yy - 0.4), (xx + w_ - 0.8, yy + 1.8 + row * 0.3)])
                xx += w_
            yy += 3.4 + row * 0.9
            row += 1
        B.detail_lines(cr, arcs, 0.4, INK, 0.38)
        stipple(cr, -6, y, 206, self.DH, 120, "#4a443c", 0.25, (0.2, 0.5), seed=21)
        cr.set_source(core.linear(0, y - 2, 0, y + 9, [(0.0, (0.15, 0.1, 0.12, 0.35)), (1.0, (0.15, 0.1, 0.12, 0.0))]))
        cr.rectangle(-6, y - 2, 212, 11)
        cr.fill()
        B.detail_lines(cr, [[(-6, 281.5), (206, 281.0)]], 0.5, INK, 0.3, taper=(1.0, 1.0, 1.0))
        cr.restore()
        # --- three house fronts, each its own character
        bone = P["bone"]
        specs = (
            dict(x=2.0, w=56.0, hg=42.0, hu=30.0, roof_h=31.0, wall=core.mix(bone, P["ochre"], 0.12), roof_c=P["sienna"],
                 shutters=P["verdigris"], roof="gable", timber="x", door_u=0.66, low_u=0.22, ups_u=(0.27, 0.73), seed=71,
                 stone=core.mix(bone, P["stone"], 0.55)),
            dict(x=73.0, w=54.0, hg=40.0, hu=34.0, roof_h=22.0, wall=core.mix(bone, P["ochre"], 0.42), roof_c=P["madder"],
                 shutters=P["ultramarine"], roof="hip", timber="close", door_u=0.6, low_u=0.2, ups_u=(0.27, 0.73), seed=80,
                 chimney=(114.0, 13.0), dormer=True, stone=core.mix(bone, "#b3a28a", 0.6)),
            dict(x=143.0, w=55.0, hg=40.0, hu=27.0, roof_h=24.0, wall=core.mix(bone, P["rose"], 0.42), roof_c="#b68e4e",
                 shutters=P["olive"], roof="thatch", timber="arch", door_u=0.37, low_u=0.78, ups_u=(0.28, 0.72), seed=89,
                 chimney=(183.0, 10.0), stone=core.mix(bone, "#a9a0a8", 0.6)),
        )
        self._houses = []
        for k, sp_ in enumerate(specs):
            sp_ = dict(sp_)
            seed_ = sp_.pop("seed")
            hf = town_house(cr, sp_.pop("x"), y, sp_.pop("w"), sp_.pop("hg"), sp_.pop("hu"), sp_.pop("roof_h"),
                            sp_.pop("wall"), sp_.pop("roof_c"), sp_.pop("shutters"), seed_, **sp_)
            # the lower window beside the door (a sill for the potions)
            lx, ly, lw_, lh = hf["low"]
            lit_window(cr, lx, ly, lw_, lh, 0.0, arch=True)
            seg_ink(cr, [(lx - 1.4, ly + lh + 0.5), (lx + lw_ + 1.4, ly + lh + 0.5)], 1.4, P["umber"], 0.95)
            self._houses.append(hf)
        # trade signs on scrolled iron brackets (the boards swing in anim): the locksmith's gilt
        # key on the first house -- and on the middle house, the baker's gilt loaf (the bread was in
        # this town all along)
        self._signs = []
        for k, (kind, side) in enumerate((("key", 1), ("loaf", 1))):
            hf = self._houses[k]
            sx_ = hf["xr"] if side > 0 else hf["xl"]
            sy_ = hf["top"] + 9.0
            arm = 9.5
            seg_ink(cr, [(sx_, sy_), (sx_ + side * arm, sy_)], 0.9, "#2e2a28", 1.0)
            B.detail_line(cr, spiral_pts(sx_ + side * 2.4, sy_ + 2.6, 0.3, 2.3, turns=1.0, n=10, a0=-math.pi * 0.5,
                                         cw=side), 0.5, "#2e2a28", 0.95, taper=(0.5, 1.0, 0.5))
            self._signs.append((sx_ + side * (arm - 1.5), sy_, kind, side))
        # iron lanterns on brackets from the next house's corner (they swing in anim)
        self._lamps = [(self._houses[1]["xl"], self._houses[1]["jetty"] - 1.0, -1),
                       (self._houses[2]["xl"], self._houses[2]["jetty"] - 1.0, -1)]

    def anim(self, cr, t):
        if not hasattr(self, "_houses"):
            return
        e = self.e
        rng = random.Random(self.seed + 99)
        # --- sky life: twinkles, the moon's glint, birds going home
        for i, (sx_, sy_, r) in enumerate(self._stars):
            a = 0.5 + 0.5 * math.sin(t * (1.1 + 0.31 * (i % 4)) + i * 2.3)
            if a > 0.6:
                fx.sparkle(cr, sx_, sy_, r * 1.9 * a, "#fff6d8", 0.55 * (a - 0.6) / 0.4 + 0.15)
        for k in range(3):
            u = (t * 0.03 + k * 0.29) % 1.0
            bx, by = -12 + u * 230, 40 + 22 * math.sin(u * 4.0 + k) + k * 11
            fl = 1.4 * math.sin(t * 7.5 + k * 2.0)
            sb.ink(cr, [(bx - 3.0, by - 1.0 - fl), (bx, by), (bx + 3.0, by - 1.0 - fl)], 0.7, INK, 0.7, (0.3, 1.0, 0.3))
        # --- the castle: pennants fly, windows light up one by one on "kingdom of stone"
        for i, (x, y) in enumerate(self._tips):
            sb.ink(cr, [(x, y + 1.0), (x, y - 7.0)], 0.6, INK, 0.9)
            sb._pennant(cr, x, y - 7.0, 11.0 if i < 2 else 13.0, t, i * 1.7, P["vermilion"] if i < 2 else P["gold"])
        tl0 = e("castle_lights")
        for k, (wx, wy) in enumerate(self._cwin):
            on = smooth((t - (tl0 + k * 0.11)) / 0.35)
            if on > 0.01:
                fl = 0.9 + 0.1 * math.sin(t * 9.0 + k * 1.7)
                soft_glow(cr, wx + 1.3, wy + 2.5, 5.0, "#ffbf5a", 0.4 * on * fl)
                sb.wash(cr, [(wx, wy), (wx + 2.6, wy), (wx + 2.6, wy + 5.0), (wx, wy + 5.0)], "#ffd97a", 0.95 * on, 0.0)
        # --- the town
        y = self.STREET_Y
        rain_u = smooth((t - e("rain")) / 0.9)
        dim = 0.35 * rain_u                     # the street darkens under the rain
        # chimney smoke: soft lilac puffs curling up and away (leaning harder once it rains)
        for i, hf in enumerate(self._houses):
            if "chimney" not in hf:
                continue
            cx_, cy_ = hf["chimney"]
            for j in range(5):
                u = (t * 0.14 + j * 0.2 + i * 0.37) % 1.0
                px_ = cx_ + u * (8.0 + 10.0 * rain_u) + 2.2 * math.sin(u * 4.0 + i * 2.0 + j)
                py_ = cy_ - 1.5 - u * 24.0
                soft_glow(cr, px_, py_, 2.6 + 6.5 * u, "#e2d8ea", 0.34 * math.sin(math.pi * min(1.0, u * 1.15)) * (1.0 - 0.3 * rain_u))
        # lamplight pools on the cobbles under the two lanterns (they flicker)
        for i, (lx_, ly_, side_) in enumerate(self._lamps):
            fl = 0.85 + 0.15 * math.sin(t * 9.0 + i * 2.0) * math.sin(t * 5.3 + i)
            cr.save()
            cr.translate(lx_ + side_ * 7.6, y + 7.0)
            cr.scale(1.0, 0.32)
            soft_glow(cr, 0.0, 0.0, 26.0, "#ffbf5a", 0.3 * fl * (1.0 - 0.45 * rain_u))
            cr.restore()
        # upper windows: a lone figure in each, lamplit, on "living alone"; the shutters swing shut
        # one after another on "latch" and an iron bar drops across each pair
        alone0 = e("alone")
        latch0 = e("latch") - LATCH_LEAD
        sleeper = (2, 0)                        # (house, window) where someone drinks a potion and yawns
        for k, hf in enumerate(self._houses):
            for j, rect in enumerate(hf["ups"]):
                idx = k * 2 + j
                lit = smooth((t - (alone0 + 0.16 * idx)) / 0.4)
                ts = latch0 + LATCH_STEP * idx
                close = core.ease("inout_back", clamp((t - ts) / LATCH_CLOSE)) if t > ts else 0.0
                shut = smooth(clamp(close))
                x, y0, w, h = rect
                if lit > 0.02:                  # warm lamplight spilling onto the plaster round it
                    soft_glow(cr, x + w * 0.5, y0 + h * 0.55, w * 1.25, "#ffbf5a", 0.22 * lit * (1.0 - 0.75 * shut))
                lit_window(cr, x, y0, w, h, lit * (1.0 - 0.85 * shut), arch=False)
                if lit > 0.05 and close < 0.6:
                    self._silhouette(cr, x + w * 0.5, y0 + h, w, lit * (1.0 - smooth(close / 0.6)), t, idx,
                                     sleepy=(k, j) == sleeper)
                bar = clamp((t - (ts + LATCH_CLOSE)) / LATCH_BAR) if t > ts + LATCH_CLOSE else 0.0
                draw_town_shutters(cr, rect, min(1.0, close) if close > 0 else 0.0, hf["shutters"],
                                   glow=lit * 0.8 if close >= 0.97 else 0.0, latch=bar, t=t)
                ink_clack(cr, x + w * 0.8, y0 + h * 0.5, w * 0.42, (t - (ts + LATCH_CLOSE + LATCH_BAR * 0.7)) / 0.35,
                          alpha=0.8, n=4, a0=-1.9, a1=-0.2)
        # the ink z's from the sleepy window
        zt = e("sleeping")
        if zt - 0.2 < t < zt + 3.2:
            hf = self._houses[sleeper[0]]
            x, y0, w, h = hf["ups"][sleeper[1]]
            for q in range(3):
                u = (t - (zt + q * 0.38)) / 1.9
                if 0.0 < u < 1.0:
                    zx, zy = x + w * 0.9 + u * 9.0 + 2.0 * math.sin(u * 6.0 + q), y0 - 1.0 - u * 16.0
                    sz = 2.0 + 2.4 * u
                    core.text(cr, "z", zx, zy, sz * 2.0, sb.TEXT_FONT, INK, align="center", italic=True,
                              alpha_=0.85 * math.sin(math.pi * u))
        # potions on the lower sills (glint on "potions"); charms by the doors (swing on "charms")
        pt0, ct0 = e("potions"), e("charms")
        for k, hf in enumerate(self._houses):
            lx, ly, lw_, lh = hf["low"]
            for q in range(2):
                bx_ = lx + lw_ * (0.3 + 0.42 * q)
                by_ = ly + lh + 0.2
                col = (P["ultramarine"], "#6b4fa0", P["verdigris"])[(k + q) % 3]
                bh = 5.4 + 1.4 * ((k + q) % 2)
                bottle = [(bx_ - 1.9, by_), (bx_ - 2.1, by_ - bh * 0.55), (bx_ - 0.7, by_ - bh * 0.72), (bx_ - 0.6, by_ - bh),
                          (bx_ + 0.6, by_ - bh), (bx_ + 0.7, by_ - bh * 0.72), (bx_ + 2.1, by_ - bh * 0.55), (bx_ + 1.9, by_)]
                pb = sb.wash(cr, bottle, col, 0.95, 0.3, smooth_t=0.4)
                sb.ink_outline(cr, pb, 0.35, INK, 0.85)
                g = math.exp(-max(0.0, t - (pt0 + 0.1 * (k * 2 + q))) / 0.5) if t > pt0 + 0.1 * (k * 2 + q) else 0.0
                pulse = 0.25 + 0.15 * math.sin(t * 2.0 + k + q)
                soft_glow(cr, bx_, by_ - bh * 0.4, 4.5, "#8fb8ff", (pulse + 0.7 * g) * (1.0 - 0.5 * dim))
                if g > 0.05:      # the cork catches the light: a cold gleam slides up the glass
                    B.detail_line(cr, [(bx_ - 1.0, by_ - bh * 0.25), (bx_ - 1.2, by_ - bh * (0.25 + 0.4 * g))], 0.45,
                                  "#eef6ff", 0.9 * g, taper=(0.2, 1.0, 0.2))
            # the charm: a rune-stone on a cord hanging by the door, swinging
            dx, dy, dw, dh = hf["door"]
            hx = dx + dw + 3.6 if k < 2 else dx - 3.6
            hy = dy - 2.0
            kick = math.exp(-max(0.0, t - (ct0 + 0.12 * k)) / 1.2) * (1.0 if t > ct0 + 0.12 * k else 0.0)
            ang = 0.12 * math.sin(t * 1.6 + k) + 0.55 * kick * math.sin((t - ct0) * 6.0)
            ang += 0.25 * rain_u * math.sin(t * 3.1 + k)
            ex_, ey_ = hx + math.sin(ang) * 6.5, hy + math.cos(ang) * 6.5
            sb.ink(cr, [(hx, hy), (ex_, ey_)], 0.35, INK, 0.9)
            stn = [(ex_ - 1.6, ey_), (ex_ - 0.6, ey_ - 0.8), (ex_ + 1.5, ey_ - 0.3), (ex_ + 1.7, ey_ + 1.8), (ex_ - 0.4, ey_ + 2.6),
                   (ex_ - 1.8, ey_ + 1.4)]
            pst = sb.wash(cr, stn, P["slate"], 0.98, 0.3, smooth_t=0.5)
            sb.ink_outline(cr, pst, 0.3, INK, 0.85)
            cg = 0.3 + 0.7 * kick
            soft_glow(cr, ex_, ey_ + 1.0, 3.6, P["rune"], 0.35 * cg)
            sb.ink(cr, [(ex_ - 0.6, ey_ + 0.4), (ex_ + 0.3, ey_ + 1.4), (ex_ + 0.8, ey_ + 0.2)], 0.3, P["rune"], 0.5 + 0.5 * cg)
        # the doors: open while their folk come home, SLAM on "lock" and the heart padlocks snap
        # shut (a little 'clack' of ink); on "heart" the candlelight burnishes each lock in turn
        lock0, heart0 = e("lock"), e("heart")
        for k, hf in enumerate(self._houses):
            o0, o1 = self._door_plan(k)
            open_ = 0.0
            t_slam = lock0 + 0.04 * k
            if o0 <= t < t_slam:
                open_ = smooth((t - o0) / 0.35) * 0.8
            slam = t - t_slam
            if slam >= 0.0:
                open_ = 0.8 * (1.0 - core.in_quad(clamp(slam / 0.09)))
            tl_ = t_slam + PADLOCK_DELAY
            lk = core.out_back(clamp((t - tl_) / 0.1)) if t > tl_ else 0.0
            swing = 0.0
            if t > tl_:
                swing = -0.32 * math.exp(-(t - tl_) / 0.32) * math.sin((t - tl_) * 15.0)
            else:
                swing = 0.05 * math.sin(t * 1.9 + k * 1.3) - 0.12 * open_ * 0.0
            glint = 0.0
            if t > heart0 + 0.12 * k:
                gu = (t - (heart0 + 0.12 * k)) / 0.6
                glint = gu if gu < 1.0 else 0.0
            lamp = clamp(open_ / 0.4) * (1.0 if t < t_slam + 0.09 else 0.0)
            draw_town_door(cr, hf["door"], open_=open_, slam=slam - 0.09 if slam > 0.09 else -1.0, t=t, lock=clamp(lk, 0.0, 1.08),
                           swing=swing, glint=glint, lamp=lamp)
            dx, dy, dw, dh = hf["door"]
            if lk > 0.0:
                ink_clack(cr, dx + dw * 0.8, dy + dh * 0.47 + dw * 0.3, dw * 0.42, (t - tl_) / 0.4, n=5, a0=-0.3, a1=1.0)
            if 0.09 < slam < 0.55:                    # SLAM: ink impact strokes round the door, a puff of dust
                u = (slam - 0.09) / 0.46
                al = math.sin(math.pi * min(1.0, u * 1.6)) * (1.0 - u)
                strokes = []
                for j, (ax, ay, a_) in enumerate(((dx - 2.2, dy + dh * 0.2, 3.5), (dx - 2.5, dy + dh * 0.5, 3.1),
                                                   (dx + dw + 2.2, dy + dh * 0.25, -0.4), (dx + dw + 2.5, dy + dh * 0.55, 0.0),
                                                   (dx + dw * 0.5, dy - 3.0, -1.57))):
                    r0, r1 = 1.0 + 2.5 * u, 3.5 + 3.5 * u
                    strokes.append([(ax + math.cos(a_) * r0, ay + math.sin(a_) * r0), (ax + math.cos(a_) * r1, ay + math.sin(a_) * r1)])
                B.detail_lines(cr, strokes, 0.55, INK, 0.85 * al, taper=(0.4, 1.0, 0.2))
                for q in (-1, 1):     # a soft puff of dust squeezed out along the threshold
                    soft_glow(cr, dx + dw * 0.5 + q * (dw * 0.45 + 5.0 * u), dy + dh - 1.2 - 0.8 * u, 2.2 + 3.2 * u,
                              "#e4dccf", 0.5 * (1.0 - u))
        # the trade signs, rocking on their brackets (harder in the rain)
        for i, (sx_, sy_, kind, side) in enumerate(self._signs):
            ang = 0.07 * math.sin(t * 1.3 + i * 1.9) + 0.12 * rain_u * math.sin(t * 2.7 + i)
            cr.save()
            cr.translate(sx_, sy_)
            cr.rotate(ang)
            seg_ink(cr, [(-2.6, 0.0), (-2.6, 2.4)], 0.4, "#2e2a28", 0.95)
            seg_ink(cr, [(2.6, 0.0), (2.6, 2.4)], 0.4, "#2e2a28", 0.95)
            board = [(-4.6, 2.4), (4.6, 2.4), (4.6, 10.2), (0.0, 12.0), (-4.6, 10.2)]
            pbd = sb.wash(cr, board, P["ultramarine"] if kind == "key" else P["madder"], 0.99, 0.3)
            sb.ink_outline(cr, pbd, 0.45, INK, 0.9)
            if kind == "key":
                cr.new_path()
                core.circle(cr, -1.8, 6.6, 1.5)
                gp = B.Path(cr)
                sb.gild(cr, path=gp, shimmer=0.5, outline=0.2)
                cr.new_path()
                core.circle(cr, -1.8, 6.6, 0.6)
                core.src(cr, P["ultramarine"])
                cr.fill()
                sb.gild(cr, [(-0.4, 6.1), (3.4, 6.1), (3.4, 7.1), (-0.4, 7.1)], shimmer=0.5, outline=0.15)
                sb.gild(cr, [(2.2, 7.0), (3.0, 7.0), (3.0, 8.4), (2.2, 8.4)], shimmer=0.5, outline=0.1)
            else:
                lp = [(-3.0, 8.6), (-2.6, 5.6), (0.0, 4.4), (2.6, 5.6), (3.0, 8.6)]
                sb.gild(cr, lp, shimmer=0.55, smooth_t=0.6, outline=0.2)
                B.detail_lines(cr, [[(-1.6, 5.6), (-0.8, 7.6)], [(0.0, 5.0), (0.0, 7.6)], [(1.6, 5.6), (0.8, 7.6)]], 0.25,
                               P["gold_dk"], 0.8)
            cr.restore()
        # the lanterns on their brackets (they sway harder in the rain)
        for i, (bx, by, side_) in enumerate(self._lamps):
            town_lantern(cr, bx, by, t * (1.0 + 0.8 * rain_u), phase=i * 2.1, scale=0.85, side=side_)
        # a candle in the baker's dormer
        if "dormer" in self._houses[1]:
            dx_, dy_, dw_, dh_ = self._houses[1]["dormer"]
            lit_window(cr, dx_, dy_, dw_, dh_, 0.75 + 0.1 * math.sin(t * 3.0), arch=True)
        # folk in the street
        self._street_folk(cr, t, rain_u)
        # the rain: painted streaks over the town (and a cold wash that dims it)
        if rain_u > 0.01:
            cr.save()
            cr.rectangle(-4, -4, self.DW + 8, self.DH + 8)
            cr.set_source(core.linear(0, 0, 0, self.DH, [(0.0, core.alpha("#141a38", 0.10 * rain_u)),
                                                        (0.55, core.alpha("#1a2240", 0.16 * rain_u)),
                                                        (1.0, core.alpha("#1a2240", 0.26 * rain_u))]))
            cr.fill()
            streaks = []
            for i in range(110):
                ph = core.hash01(i, 5)
                sp = 52.0 + 22.0 * core.hash01(i, 6)
                yy = ((ph * 300.0 + t * sp) % 300.0) - 10.0
                xx = core.hash01(i, 7) * 240.0 - 25.0 + yy * 0.16
                streaks.append([(xx, yy), (xx + 1.0, yy + 6.5)])
            B.detail_lines(cr, streaks, 0.45, "#d2def2", 0.5 * rain_u, taper=(0.3, 1.0, 0.3))
            cr.restore()

    def _door_plan(self, k):
        """When each house's door opens to let its owner in (the door shuts on "lock")."""
        lock0 = self.e("lock")
        return (lock0 - 0.95 + 0.2 * k, lock0)

    def _silhouette(self, cr, x, y_sill, w, a, t, idx, sleepy=False):
        """A lone figure in a lamplit window: a dark head-and-shoulders shape, sometimes turning away."""
        cr.save()
        cr.rectangle(x - w * 0.5, y_sill - w * 2.2, w, w * 2.2)
        cr.clip()
        rock = 0.6 * math.sin(t * 0.9 + idx * 1.7)
        kinds = ("goblin", "elf", "mouse", "hare", "dwarf", "kobold")
        kind = kinds[idx % len(kinds)]
        hx, hy = x + rock * 0.4, y_sill - w * 0.66
        hr = w * 0.21
        side = 1.0 if idx % 2 == 0 else -1.0          # which way the profile looks
        cr.new_path()
        # shoulders: a soft hump resting on the sill
        core.smooth_closed(cr, [(x - w * 0.46, y_sill + 1.0), (x - w * 0.4, y_sill - w * 0.22), (x - w * 0.18, y_sill - w * 0.36),
                                (x + w * 0.18, y_sill - w * 0.36), (x + w * 0.4, y_sill - w * 0.22), (x + w * 0.46, y_sill + 1.0)], 0.6)
        core.circle(cr, hx, hy, hr)                                       # the head
        core.ellipse(cr, hx + side * hr * 0.9, hy + hr * 0.25, hr * 0.55, hr * 0.32)   # muzzle / nose in profile
        if kind == "goblin":
            for sg in (-1.0, 1.0):
                core.polygon(cr, [(hx + sg * hr * 0.7, hy - hr * 0.35), (hx + sg * hr * 2.3, hy - hr * 0.75), (hx + sg * hr * 0.8, hy + hr * 0.15)])
        elif kind == "elf":
            for sg in (-1.0, 1.0):
                core.polygon(cr, [(hx + sg * hr * 0.6, hy - hr * 0.2), (hx + sg * hr * 1.7, hy - hr * 1.6), (hx + sg * hr * 0.9, hy + hr * 0.1)])
        elif kind == "mouse":
            for sg in (-1.0, 1.0):
                core.circle(cr, hx + sg * hr * 0.75, hy - hr * 0.85, hr * 0.55)
        elif kind == "hare":
            for sg in (-1.0, 1.0):
                core.ellipse(cr, hx + sg * hr * 0.4, hy - hr * 1.7, hr * 0.28, hr * 0.95, sg * 0.12)
        elif kind == "dwarf":
            core.polygon(cr, [(hx - hr * 1.0, hy - hr * 0.4), (hx + hr * 0.2, hy - hr * 2.6), (hx + hr * 1.0, hy - hr * 0.4)])
            core.ellipse(cr, hx, hy + hr * 0.9, hr * 0.85, hr * 0.8)
        else:
            for sg in (-1.0, 1.0):
                core.polygon(cr, [(hx + sg * hr * 0.3, hy - hr * 0.8), (hx + sg * hr * 0.75, hy - hr * 1.7), (hx + sg * hr * 0.75, hy - hr * 0.6)])
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)
        core.src(cr, "#3a2416", 0.88 * a)
        cr.fill()
        # a warm rim where the lamp behind them catches the edge
        cr.new_path()
        cr.arc(hx, hy, hr, -2.4 if side > 0 else -0.7, -0.6 if side > 0 else 0.9)
        cr.set_line_width(max(0.25, hr * 0.18))
        core.src(cr, "#ffcf7a", 0.55 * a)
        cr.stroke()
        if sleepy:
            zt = self.e("sleeping")
            pt0 = self.e("potions")
            # lifts a little blue bottle on "potions", sips, yawns on "sleeping"
            lift = smooth((t - pt0) / 0.4) * (1.0 - smooth((t - (zt - 0.1)) / 0.4))
            if lift > 0.02:
                bx_, by_ = hx + w * 0.3, lerp(y_sill, hy + w * 0.1, lift)
                sb.wash(cr, [(bx_ - 0.9, by_), (bx_ + 0.9, by_), (bx_ + 0.7, by_ - 2.6), (bx_ - 0.7, by_ - 2.6)],
                        P["ultramarine"], 0.95 * a, 0.0)
            yawn = math.sin(math.pi * clamp((t - zt) / 0.8))
            if yawn > 0.02:
                cr.new_path()
                core.ellipse(cr, hx + w * 0.12, hy + w * 0.08, w * 0.07 * yawn + 0.1, w * 0.12 * yawn + 0.1)
                core.src(cr, "#ffcf7a", 0.9 * a)
                cr.fill()
        cr.restore()

    def folk_plan(self):
        """Waypoints (t, x) of the two walkers, ending in their own doorways. They cross at ev
        "cross" without a word (the elf glances, the goblin turns his face away), amble while it is
        dry and hurry once the rain starts."""
        e = self.e
        d = {k: self._houses[k]["door"] for k in range(3)}
        door_x = {k: d[k][0] + d[k][2] * 0.5 for k in range(3)}
        cross, rain = e("cross"), e("rain")
        tin = {k: self._door_plan(k)[0] + 0.32 for k in range(3)}
        gob = [(e("folk_walk") - 1.5, 30.0), (cross, 88.0), (rain, 99.0), (tin[1], door_x[1])]
        elf = [(e("folk_walk") - 1.5, 168.0), (cross, 90.0), (rain, 66.0), (tin[0], door_x[0])]
        return {"goblin": (gob, 1, 1, True, 1), "elf": (elf, -1, 0, False, 2)}

    @staticmethod
    def _along(keys, t):
        """Position along eased waypoints + the distance walked so far (for the walk phase)."""
        if t <= keys[0][0]:
            return keys[0][1], 0.0, 0.0
        dist = 0.0
        for (t0, x0), (t1, x1) in zip(keys, keys[1:]):
            if t < t1:
                u = (t - t0) / max(1e-6, t1 - t0)
                x = lerp(x0, x1, u)            # constant pace inside a segment (no foot sliding)
                return x, dist + abs(x - x0), abs(x1 - x0) / max(1e-6, t1 - t0)
            dist += abs(x1 - x0)
        return keys[-1][1], dist, 0.0

    def _street_folk(self, cr, t, rain_u):
        """Three folk, each alone: two cross without a word (one turns away), one fumbles with her
        own latch; when the rain comes they hurry home and vanish through their doors just before
        the doors slam on "lock"."""
        e = self.e
        y = self.STREET_Y + 9.0
        lock0 = e("lock")
        cross = e("cross")
        for kind, (keys, facing, home, lantern, seed) in self.folk_plan().items():
            dx, dy, dw, dh = self._houses[home]["door"]
            t_in = keys[-1][0]                              # reaches the open doorway
            t_gone = lock0 + 0.04 * home - 0.03             # gone into the dark before the door slams
            if t >= t_gone:
                continue
            x, dist, speed = self._along(keys, t)
            walking = clamp(speed / 6.0) if t < t_in else 0.0
            look = away = 0.0
            if kind == "elf":
                look = math.sin(math.pi * clamp((t - (cross - 0.55)) / 1.1)) * 0.9
            else:
                away = smooth((t - (cross - 0.25)) / 0.25) * (1.0 - smooth((t - (cross + 1.1)) / 0.3))
            step_in = smooth((t - t_in) / max(0.05, t_gone - t_in))
            vis = 1.0 - step_in
            yy = lerp(y, dy + dh + 0.6, step_in)
            fac = facing
            if t >= t_in - 0.05:
                away = max(away, smooth((t - (t_in - 0.05)) / 0.15))     # turns into the doorway
            pfolk(cr, x, yy, 0.78 * (1.0 - 0.14 * step_in), kind, t, facing=fac, walk=walking, phase=dist / 8.5,
                  hurry=rain_u, away=away, look=look, lantern=lantern, alpha=vis, seed=seed)
        # the mouse-folk: at her own door all along, back to us, fumbling with her latch; in she goes
        home = 2
        dx, dy, dw, dh = self._houses[home]["door"]
        t_in = self._door_plan(home)[0] + 0.32
        t_gone = lock0 + 0.04 * home - 0.03
        if t < t_gone:
            step_in = smooth((t - t_in) / max(0.05, t_gone - t_in))
            fumble = 0.55 + 0.25 * math.sin(t * 4.2) * (1.0 - step_in)
            pfolk(cr, dx + dw * 0.5, lerp(y - 1.0, dy + dh + 0.6, step_in), 0.74 * (1.0 - 0.14 * step_in), "mouse", t,
                  facing=1, away=1.0, reach=fumble, alpha=1.0 - step_in, seed=3, hurry=rain_u * 0.6)


# ----------------------------------------------------------------------------------------
# verse 2: the dragon's street (left) and the merchants' market (right)
# ----------------------------------------------------------------------------------------

def storybook_dragon_posed(cr, x, y, s, t, pose, alpha=0.97, tint=0.14):
    """THE DRAGON on-model (the real rig) painted into a page: soft storybook light, then washed a
    little toward the parchment so he sits in the paint. Returns his rig."""
    cr.push_group()
    rig = ch.draw_dragon(cr, x, y, s, pose, sb.STORYBOOK_LIGHT, t)
    pat = cr.pop_group()
    cr.save()
    cr.set_source(pat)
    cr.paint_with_alpha(alpha)
    core.src(cr, sb.PARCHMENT, tint)
    cr.mask(pat)
    cr.restore()
    return rig


def _dusk_sky(cr, DW, DH, bottom, seed):
    sb._sky(cr, DW, DH, [(0.0, "#232a5a"), (0.35, "#4a4884"), (0.62, "#8a6a92"), (0.85, "#d0908a"),
                         (1.0, "#ebb98e")], seed=seed, blooms=6, bottom=bottom)


def _far_roofs(cr, y, seed, color="#8a83a6", lit=0.0):
    """A hazy row of distant gabled houses (and a church spire) standing on the line y."""
    rng = random.Random(seed)
    x = -12.0
    wins = []
    while x < 214:
        w = rng.uniform(14, 24)
        h = rng.uniform(10, 18)
        rh = rng.uniform(6, 11)
        body = [(x, y), (x, y - h), (x + w * 0.5, y - h - rh), (x + w, y - h), (x + w, y)]
        sb.wash(cr, body, core.mix(color, "#6a6488", rng.uniform(0, 0.4)), 0.88, 0.2)
        if rng.random() < 0.55:
            wins.append((x + w * rng.uniform(0.25, 0.6), y - h * rng.uniform(0.35, 0.7)))
        x += w + rng.uniform(-3, 1)
    sx = 40.0 + 120.0 * rng.random()
    sb.wash(cr, [(sx - 3, y - 12), (sx - 3, y - 24), (sx, y - 40), (sx + 3, y - 24), (sx + 3, y - 12)], "#7a7498", 0.9, 0.2)
    for (wx, wy) in wins:
        sb.wash(cr, [(wx, wy), (wx + 1.8, wy), (wx + 1.8, wy + 2.4), (wx, wy + 2.4)],
                core.mix("#3c3a58", "#ffcf7a", lit), 0.9, 0.0)


class DragonStreet(_Synced):
    """Verse 2, left page: the dragon -- on-model, the real rig -- in his charcoal-navy coat and
    mustard scarf on a cobbled dusk street, the far castle above the roofs. "with a scarf and a
    sigh": he sighs (a curl of smoke); "And he waved at his neighbours": he waves, hopeful; "who
    hurried on by": three folk hurry past, heads down (the kobold glances and speeds up) and his
    wave sinks. "But for what he was missing": the cold glow of the merchants' wares spills across
    the gutter onto his page and he turns toward it; "there wasn't a spell": he turns away, head
    down, and the cold light dies."""
    DW, DH = 200.0, 212.0
    grain = 0.3
    GROUND = 176.0

    def back(self, cr):
        _dusk_sky(cr, self.DW, self.DH, 150, self.seed + 3)
        for (sx_, sy_, r) in ((30, 20, 2.4), (74, 12, 1.8), (120, 26, 2.0), (176, 14, 2.6), (150, 44, 1.6)):
            gold_star(cr, sx_, sy_, r)
        stipple(cr, 0, 0, self.DW, 80, 24, "#fff6dc", 0.3, (0.2, 0.4), seed=self.seed + 4)
        # verse 1's castle, far away on its hill above the roofs
        hill = [(48, 132), (76, 108), (100, 98), (124, 108), (152, 132), (152, 140), (48, 140)]
        sb.wash(cr, hill, "#7686a0", 0.85, 0.25, smooth_t=0.5)
        st = "#8f94ac"
        sb.wash(cr, [(88, 100), (88, 88), (112, 88), (112, 100)], st, 0.9, 0.2)
        for (tx, top, tw, rc) in ((84, 82, 6.0, "#a8607a"), (110, 82, 6.0, "#a8607a"), (96.5, 68, 7.0, "#9a5a72")):
            sb.wash(cr, [(tx, 100), (tx, top), (tx + tw, top), (tx + tw, 100)], st, 0.9, 0.2)
            sb.wash(cr, [(tx - 1.2, top), (tx + tw * 0.5, top - tw * 1.5), (tx + tw + 1.2, top)], rc, 0.88, 0.2)
        for (wx, wy) in ((90.5, 92), (99.5, 76), (112.5, 90)):
            sb.wash(cr, [(wx, wy), (wx + 1.6, wy), (wx + 1.6, wy + 3), (wx, wy + 3)], "#ffd27a", 0.9, 0.0)
        _far_roofs(cr, 136.0, self.seed + 5, lit=0.6)
        # the two house fronts framing the street, dressed: the left one lamplit (they're home,
        # they just don't come out), the right one dark
        hl = town_house(cr, -14.0, self.GROUND, 72.0, 54.0, 44.0, 34.0, core.mix(P["bone"], P["ochre"], 0.3),
                        P["madder"], P["verdigris"], self.seed + 1, roof="gable", timber="x", door_u=0.62, low_u=0.24,
                        ups_u=(0.3, 0.72), jetty=4.0)
        dress_town_house(cr, hl, lit=(0.85, 0.6), flowers=(P["vermilion"], P["ochre"], P["rose"]), seed=7)
        hr = town_house(cr, 142.0, self.GROUND, 72.0, 54.0, 42.0, 26.0, core.mix(P["bone"], P["rose"], 0.32),
                        P["sienna"], P["ultramarine"], self.seed + 2, roof="hip", timber="close", door_u=0.4, low_u=0.78,
                        ups_u=(0.3, 0.7), jetty=4.0, chimney=(198.0, 12.0))
        dress_town_house(cr, hr, lit=(0.5, 0.3), shut=(True, True))
        # the street
        street = [(-6, self.GROUND - 1.0), (206, self.GROUND - 1.0), (206, self.DH + 4), (-6, self.DH + 4)]
        ps = sb.wash(cr, street, "#a39a8c", 0.95, 0.3)
        cr.save()
        ps.add(cr)
        cr.clip()
        rng = random.Random(self.seed + 9)
        arcs = []
        yy = self.GROUND + 1.0
        row = 0
        while yy < self.DH + 4:
            xx = -8.0 - (row % 2) * 4.0
            ww_ = 7.0 + row * 1.2
            while xx < 210:
                w_ = rng.uniform(ww_ * 0.85, ww_ * 1.2)
                arcs.append([(xx + 0.8, yy + 2.0 + row * 0.3), (xx + w_ * 0.5, yy - 0.4), (xx + w_ - 0.8, yy + 2.0 + row * 0.3)])
                xx += w_
            yy += 3.6 + row * 1.0
            row += 1
        B.detail_lines(cr, arcs, 0.4, INK, 0.35)
        stipple(cr, -6, self.GROUND, 206, self.DH, 90, "#4a443c", 0.22, (0.2, 0.5), seed=31)
        cr.restore()
        # the iron lantern post
        sb.ink(cr, [(156, self.GROUND + 6), (156, 96)], 2.6, "#2e2a28", 1.0, (1.0, 1.0, 0.8))
        sb.ink(cr, [(156, 98), (164, 96)], 1.2, "#2e2a28", 1.0)
        sb.ink(cr, [(152, self.GROUND + 6), (160, self.GROUND + 6)], 2.0, "#2e2a28", 1.0)

    def offer(self, t):
        e = self.e
        return smooth((t - (e("but") + 0.2)) / 0.5) * (1.0 - smooth((t - (e("wasnt", e("spell") - 0.75))) / 0.5))

    PASS_SPEED = 84.0                        # design units / s: a scurry, quick small steps

    def passers(self):
        """(kind, start time, glance, bundle): the neighbours who hurry by during "neighbours,
        who hurried on by"."""
        e = self.e
        t0 = e("wave") - 0.25                 # already coming up the street as he raises his hand
        return (("goblin", t0, 0.0, None), ("kobold", t0 + 0.36, 1.0, None), ("mouse", t0 + 0.74, 0.0, P["ochre"]))

    def passer_at(self, t, t0, glance):
        """x, distance walked, glance amount (or None when off the picture)."""
        if t < t0:
            return None, 0.0, 0.0
        dist = (t - t0) * self.PASS_SPEED
        # the glancer slows a beat as she passes him, looks, then speeds up
        if glance > 0:                       # level with him: a glance up, a hitch, then faster away
            tg = t0 + 1.3
            dist -= 10.0 * smooth((t - tg) / 0.3) - 10.0 * smooth((t - (tg + 0.45)) / 0.25)
        x = -30.0 + dist
        if x > 240.0:
            return None, 0.0, 0.0
        g = glance * math.sin(math.pi * clamp((t - (t0 + 1.15)) / 0.75))
        return x, dist, g

    def pose(self, t):
        e = self.e
        sig, wav, hur = e("sigh"), e("wave"), e("hurried")
        by_, but_, spell = e("by"), e("but"), e("spell")
        wasnt = e("wasnt", spell - 0.75)
        sigh = smooth((t - (sig - 0.08)) / 0.22) * (1.0 - smooth((t - (sig + 0.6)) / 0.6))
        sigh = max(sigh, 0.5 * smooth((t - (wasnt + 0.2)) / 0.4) * (1.0 - smooth((t - (spell + 1.4)) / 0.6)))
        w_in = core.out_back(clamp((t - (wav - 0.2)) / 0.32)) if t > wav - 0.2 else 0.0
        w_out = core.inout_sine(clamp((t - (by_ - 0.45)) / 0.9))
        amt = clamp(w_in) * (1.0 - w_out)
        hope = smooth((t - (wav - 0.3)) / 0.3) * (1.0 - smooth((t - (hur + 0.2)) / 0.6))
        look_x = 0.35 * math.sin(t * 0.7) * (1.0 - hope)
        # his eyes follow the passers-by as they go (eyes first, the head after)
        t_pass = self.passers()[0][1]
        follow = smooth((t - (t_pass + 0.9)) / 0.5) * (1.0 - smooth((t - (e("by") + 0.5)) / 0.6))
        look_x = lerp(look_x, 0.9, follow)
        across = self.offer(t)
        away = smooth((t - (wasnt + 0.05)) / 0.45)
        head_turn = 0.6 * across - 0.25 * away + 0.35 * smooth((t - (t_pass + 1.1)) / 0.6) * (1.0 - smooth((t - (e("by") + 0.4)) / 0.7))
        look_x = lerp(look_x, 1.0, across)
        look_x = lerp(look_x, -0.3, away)
        nod = -0.15 - 0.4 * away - 0.2 * smooth((t - (hur + 0.3)) / 0.5) * (1.0 - smooth((t - but_) / 0.3))
        look_y = 0.1 + 0.6 * away
        wings = lerp(-0.45, 0.25, hope) + 0.15 * across - 0.5 * away
        near = ch.Arm("wave", amt=amt, prev="rest", phase=(t - wav) * 0.9) if amt > 0.001 else ch.Arm("rest")
        return ch.DragonPose(facing=0, turn=0.25, mood="lonely", mood2="happy", mood_mix=hope * (1.0 - away),
                             sigh=sigh, wings=wings, head_turn=head_turn, head_nod=nod, look=(look_x, look_y), near=near,
                             far=ch.Arm("rest"), hunch=0.55 + 0.3 * away, seed=3, tail_curl=0.5)

    def anim(self, cr, t):
        e = self.e
        sb._lantern(cr, 165, 96, t, phase=0.7, scale=1.0)
        for k in range(2):
            u = (t * 0.035 + k * 0.45) % 1.0
            bx, by = -10 + u * 220, 40 + 12 * math.sin(u * 5 + k) + k * 9
            fl = 1.4 * math.sin(t * 7.0 + k)
            sb.ink(cr, [(bx - 3.0, by - 1.0 - fl), (bx, by), (bx + 3.0, by - 1.0 - fl)], 0.7, INK, 0.7, (0.3, 1.0, 0.3))
        # the cold glow of the merchants' wares, reaching across the gutter for him in streams of
        # rune-light (and drawing back again on "there wasn't a spell")
        off = self.offer(t)
        if off > 0.01:
            cr.save()
            cr.rectangle(-4, -4, self.DW + 8, self.DH + 8)
            cr.set_source(core.linear(self.DW, 0, self.DW * 0.3, 0, [(0.0, core.alpha("#7fe0ff", 0.34 * off)),
                                                                    (0.55, core.alpha("#6fb8e8", 0.12 * off)),
                                                                    (1.0, core.alpha("#6fb8e8", 0.0))]))
            cr.fill()
            for i, (y0_, y1_, ph_) in enumerate(((104.0, 128.0, 0.0), (122.0, 142.0, 1.7), (140.0, 150.0, 3.1))):
                reach = clamp(off * 1.15 - 0.08 * i)
                n = 18
                for j in range(n + 1):
                    u = j / n
                    if u > reach:
                        break
                    x_ = lerp(self.DW + 6.0, 104.0, u)
                    y_ = lerp(y0_, y1_, u) + 5.0 * math.sin(u * 5.0 + t * 2.2 + ph_)
                    soft_glow(cr, x_, y_, 6.0 + 4.0 * u, "#8fe8ff", 0.13 * off * (1.0 - 0.5 * u))
                    if j % 3 == 0:
                        sb.ink(cr, [(x_ - 1.2, y_ - 0.6), (x_ + 0.4, y_ + 0.5), (x_ + 1.4, y_ - 0.7)], 0.35, P["rune"],
                               0.6 * off * (1.0 - u))
            cr.restore()
        pose = self.pose(t)
        dx, dy, ds = 84.0, self.GROUND + 20.0, 0.232
        B.contact_shadow(cr, dx, dy, 36.0, 6.0, alpha=0.25)
        rig = storybook_dragon_posed(cr, dx, dy, ds, t, pose)
        if off > 0.01:      # the cold rim the stones throw on him
            soft_glow(cr, rig.head[0] + 14.0, rig.head[1] + 4.0, 26.0, "#8fe8ff", 0.16 * off)
        sig = e("sigh")
        if sig - 0.1 < t < sig + 3.2:
            ch.dragon_smoke(cr, t, sig + 0.05, rig, scale=1.15, dur=2.6, alpha=0.85, light_tint="#f4f0ff")
        wasnt = e("wasnt", e("spell") - 0.75)
        if wasnt < t < wasnt + 3.4:
            ch.dragon_smoke(cr, t, wasnt + 0.3, rig, scale=0.9, dur=2.4, alpha=0.7, light_tint="#f4f0ff")
        # the neighbours hurrying by in the foreground, heads down, all the same way ("on by"),
        # one after another; the kobold glances up at him and scurries faster
        y = self.DH - 11.0
        for k, (kind, t0, glance, bundle) in enumerate(self.passers()):
            x, dist, g = self.passer_at(t, t0, glance)
            if x is None:
                continue
            pfolk(cr, x, y - k * 1.2, 1.38, kind, t, facing=1, walk=1.0, phase=dist / 21.0, hurry=1.0 - 0.6 * g, look=g,
                  seed=k + 11, bundle=bundle)
        return rig


class Market(_Synced):
    """Verse 2, right page: the merchants' stalls -- STONES, POTIONS, CANDLES (the city's remedies:
    stones, all of them). On "stone" the goblin lifts a rune-stone that flares cold; on "sell" the
    dwarf and the kobold hold up a sleeping draught and a spell-candle; "But for what he was
    missing" all three hold their glowing wares out toward the dragon across the gutter (their cold
    light spills onto his page); "there wasn't a spell": they lower them and shrug."""
    DW, DH = 200.0, 212.0
    grain = 0.3
    COUNTER = 142.0
    AWN = (70.0, 88.0)

    def back(self, cr):
        _dusk_sky(cr, self.DW, self.DH, 90, self.seed + 6)
        gold_star(cr, 162, 14, 2.4)
        gold_star(cr, 36, 22, 2.0)
        hs = []
        for k, (x, w, c, rf, sh) in enumerate(((-12, 74, P["bone"], P["madder"], P["verdigris"]),
                                               (62, 76, core.mix(P["bone"], P["ochre"], 0.35), P["sienna"], P["ultramarine"]),
                                               (138, 76, core.mix(P["bone"], P["rose"], 0.3), "#5b5f7c", P["olive"]))):
            hf = town_house(cr, x, 122.0, w, 30.0, 40.0, 22.0 + (k % 2) * 6, core.mix(c, "#9a96ae", 0.2),
                            core.mix(rf, "#6c6a80", 0.25), sh, self.seed + 20 + k, jetty=3.0,
                            roof=("gable", "hip", "gable")[k], timber=("x", "close", "arch")[k])
            dress_town_house(cr, hf, lit=((0.0, 0.7), (0.5, 0.0), (0.0, 0.0))[k],
                             shut=((True, False), (False, True), (True, True))[k], door=False)
            hs.append(hf)
        street = [(-6, 118), (206, 118), (206, self.DH + 4), (-6, self.DH + 4)]
        ps = sb.wash(cr, street, "#a39a8c", 0.95, 0.3)
        cr.save()
        ps.add(cr)
        cr.clip()
        stipple(cr, -6, 118, 206, self.DH, 110, "#4a443c", 0.22, (0.2, 0.5), seed=41)
        rng = random.Random(42)
        arcs = []
        yy = 178.0
        row = 0
        while yy < self.DH + 4:
            xx = -8.0 - (row % 2) * 4.0
            while xx < 210:
                w_ = rng.uniform(8.0, 11.0)
                arcs.append([(xx + 0.8, yy + 2.0), (xx + w_ * 0.5, yy - 0.4), (xx + w_ - 0.8, yy + 2.0)])
                xx += w_
            yy += 4.6 + row
            row += 1
        B.detail_lines(cr, arcs, 0.4, INK, 0.33)
        cr.restore()
        self._stalls = []
        for k, (x, awn, sign) in enumerate(((2, P["vermilion"], "STONES"), (68, P["ultramarine"], "POTIONS"),
                                            (134, P["verdigris"], "CANDLES"))):
            w = 64.0
            for px in (x + 2.5, x + w - 2.5):
                sb.ink(cr, [(px, self.COUNTER + 34), (px, self.AWN[0] - 2)], 2.4, P["umber"], 1.0, (1.0, 1.0, 1.0))
            self._stalls.append((x, w, awn, sign))

    def offer(self, t):
        e = self.e
        return smooth((t - (e("but") + 0.2)) / 0.5) * (1.0 - smooth((t - e("wasnt", e("spell") - 0.75)) / 0.5))

    def _counter(self, cr, x, w):
        top, bot = self.COUNTER, self.COUNTER + 34
        ctr = [(x - 2, top), (x + w + 2, top), (x + w, bot), (x, bot)]
        pc = sb.wash(cr, ctr, "#8a5a36", 0.99, 0.45)
        sb.hatch(cr, pc, 1.57, 3.2, 0.4, INK, 0.28)
        sb.ink(cr, [(x - 2, top + 1.2), (x + w + 2, top + 1.2)], 1.6, "#5e3b25", 0.95)
        sb.ink_outline(cr, pc, 0.75, INK, 0.85)

    def anim(self, cr, t):
        if not hasattr(self, "_stalls"):
            return
        e = self.e
        stone, sell, spell = e("stone"), e("sell"), e("spell")
        wasnt = e("wasnt", spell - 0.75)
        off = self.offer(t)
        shrug = smooth((t - (wasnt + 0.05)) / 0.35) * (1.0 - smooth((t - (spell + 1.4)) / 0.5))
        for k, (x, w, awn, sign) in enumerate(self._stalls):
            kind = ("goblin", "frog", "kobold")[k]
            t_up = stone - 0.12 if k == 0 else sell - 0.05 + 0.14 * (k - 1)
            lift = core.out_back(clamp((t - t_up) / 0.32)) if t > t_up else 0.0
            lift = clamp(lift, 0.0, 1.15) * (1.0 - smooth((t - (wasnt - 0.1)) / 0.4))
            lift = max(lift, 0.0)
            busy = 0.5 + 0.5 * math.sin(t * 1.4 + k * 2.0)
            reach = max(0.3 * busy * (1.0 - min(1.0, lift)), off)
            ware = self._ware_cb(k, t, lift, off)
            pfolk(cr, x + w * 0.52, self.COUNTER + 19.0, 1.7, kind, t, facing=-1, reach=reach,
                  lift=min(1.0, lift) * (1.0 - 0.45 * off), hold=ware if (lift > 0.05 or off > 0.05) else None,
                  shrug=shrug, seed=k + 21, look=0.6 * (1.0 - off))
            self._counter(cr, x, w)
            self._wares(cr, x, w, k, t)
            self._awning(cr, x, w, awn, sign, k, t)

    def _ware_cb(self, k, t, lift, off):
        e = self.e

        def cb(cr, hx, hy):
            if k == 0:
                st = [(hx - 4.4, hy + 1.2), (hx - 3.2, hy - 4.0), (hx + 1.6, hy - 5.0), (hx + 4.8, hy - 1.6), (hx + 3.8, hy + 2.2),
                      (hx - 0.6, hy + 3.0)]
                flare = math.exp(-max(0.0, t - e("stone")) / 0.7) if t > e("stone") else 0.0
                soft_glow(cr, hx, hy - 1.0, 11.0 + 8.0 * flare + 4.0 * off, P["rune"], 0.4 + 0.45 * flare + 0.25 * off)
                ps = sb.wash(cr, st, P["slate"], 0.99, 0.4, smooth_t=0.6)
                sb.ink_outline(cr, ps, 0.45, INK, 0.9)
                g = 0.6 + 0.4 * math.sin(t * 3.0)
                sb.ink(cr, [(hx - 2.2, hy - 1.8), (hx + 0.2, hy + 0.4), (hx + 2.2, hy - 2.2)], 0.6, P["rune"], g)
                if flare > 0.05:
                    fx.sparkle(cr, hx + 1.5, hy - 3.4, 5.0 * flare + 1.2, "#e8fbff", 0.95 * flare)
            elif k == 1:
                bottle = [(hx - 2.6, hy + 2.2), (hx - 2.8, hy - 2.8), (hx - 0.9, hy - 3.9), (hx - 0.8, hy - 6.6),
                          (hx + 0.8, hy - 6.6), (hx + 0.9, hy - 3.9), (hx + 2.8, hy - 2.8), (hx + 2.6, hy + 2.2)]
                soft_glow(cr, hx, hy - 1.0, 9.0 + 4.0 * off, "#8fb8ff", 0.4 + 0.2 * off)
                pb = sb.wash(cr, bottle, P["ultramarine"], 0.97, 0.3, smooth_t=0.4)
                sb.ink_outline(cr, pb, 0.45, INK, 0.9)
                crs = crescent_pts(hx, hy - 0.6, 1.3, 0.7, -0.4, 1.1)
                sb.wash(cr, crs, P["gold_hi"], 0.9, 0.0)
                fx.sparkle(cr, hx - 1.0, hy - 1.8, 2.0, "#ffffff", 0.6)
            else:
                jar = [(hx - 2.8, hy + 2.8), (hx - 2.8, hy - 2.8), (hx + 2.8, hy - 2.8), (hx + 2.8, hy + 2.8)]
                pj = sb.wash(cr, jar, "#cfd8e2", 0.8, 0.3)
                sb.ink_outline(cr, pj, 0.4, INK, 0.8)
                b, sw, st_ = sb.candle_flicker(t, 31)
                soft_glow(cr, hx, hy - 5.0, 8.0 + 3.0 * off, "#c9b6ff", 0.45 * b + 0.15 * off)
                fl = [(hx - 1.0, hy - 2.8), (hx + 0.6 * sw, hy - 2.8 - 4.2 * st_), (hx + 1.0, hy - 2.8)]
                cr.new_path()
                core.smooth_closed(cr, fl + [(hx, hy - 2.2)], 0.8)
                core.src(cr, "#e2d6ff", 0.95)
                cr.fill()
        return cb

    def _wares(self, cr, x, w, k, t):
        y = self.COUNTER - 0.5
        if k == 0:
            for j in range(4):
                sx, sy = x + 10 + j * 14.5, y
                st = [(sx - 5.4, sy), (sx - 4.2, sy - 5.0), (sx + 1.6, sy - 6.6), (sx + 5.8, sy - 2.6), (sx + 4.8, sy)]
                g = 0.5 + 0.5 * math.sin(t * 2.2 + j * 1.3)
                soft_glow(cr, sx, sy - 2.8, 7.5, P["rune"], 0.24 * g)
                ps = sb.wash(cr, st, P["slate"], 0.98, 0.4, smooth_t=0.6)
                sb.ink_outline(cr, ps, 0.5, INK, 0.8)
                sb.ink(cr, [(sx - 2.0, sy - 3.8), (sx + 0.4, sy - 1.4), (sx + 2.2, sy - 4.2)], 0.6, P["rune"], 0.5 + 0.5 * g)
        elif k == 1:
            cols = (P["azure"], P["madder"], P["verdigris"], "#6b4fa0")
            for j in range(4):
                bx_, by_ = x + 10 + j * 14.5, y
                bh = 11.0 + (j % 2) * 3.5
                bottle = [(bx_ - 4.0, by_), (bx_ - 4.3, by_ - bh * 0.6), (bx_ - 1.4, by_ - bh * 0.8), (bx_ - 1.2, by_ - bh),
                          (bx_ + 1.2, by_ - bh), (bx_ + 1.4, by_ - bh * 0.8), (bx_ + 4.3, by_ - bh * 0.6), (bx_ + 4.0, by_)]
                pb = sb.wash(cr, bottle, cols[j], 0.93, 0.4, smooth_t=0.4)
                sb.ink_outline(cr, pb, 0.5, INK, 0.8)
                fx.sparkle(cr, bx_ - 1.6, by_ - bh * 0.45, 1.9, "#ffffff", 0.5)
                for b in range(2):
                    u = (t * 0.6 + j * 0.3 + b * 0.5) % 1.0
                    cr.new_path()
                    core.circle(cr, bx_ + 0.7 * math.sin(u * 9 + j), by_ - bh - 1 - u * 9, 0.8 * (1 - u) + 0.2)
                    core.src(cr, cols[j], 0.6 * (1 - u))
                    cr.fill()
        else:
            for j in range(4):
                cx_, cy_ = x + 10 + j * 14.5, y
                jar = [(cx_ - 4.6, cy_), (cx_ - 4.6, cy_ - 8), (cx_ + 4.6, cy_ - 8), (cx_ + 4.6, cy_)]
                pj = sb.wash(cr, jar, "#cfd8d2", 0.75, 0.3)
                sb.ink_outline(cr, pj, 0.45, INK, 0.7)
                hgt = 12 + j % 2 * 2.5
                cd = [(cx_ - 2.8, cy_ - 1), (cx_ - 2.8, cy_ - hgt), (cx_ + 2.8, cy_ - hgt), (cx_ + 2.8, cy_ - 1)]
                sb.wash(cr, cd, "#d8c8e8", 0.95, 0.3)
                b, sw, st_ = sb.candle_flicker(t + j, j)
                soft_glow(cr, cx_, cy_ - hgt - 3.5, 6.0, "#c9b6ff", 0.32 * b)
                fl = [(cx_ - 1.0, cy_ - hgt), (cx_ + 0.7 * sw, cy_ - hgt - 4.2 * st_), (cx_ + 1.0, cy_ - hgt)]
                cr.new_path()
                core.smooth_closed(cr, fl + [(cx_, cy_ - hgt + 0.7)], 0.8)
                core.src(cr, "#e2d6ff", 0.95)
                cr.fill()

    def _awning(self, cr, x, w, awn, sign, k, t):
        top, bot = self.AWN
        stripes = 6
        for s_ in range(stripes):
            x0, x1 = x - 4 + (w + 8) * s_ / stripes, x - 4 + (w + 8) * (s_ + 1) / stripes
            fl = 1.3 * math.sin(t * 3.0 + s_ * 0.9 + k)
            poly = [(x0 + 3.0, top), (x1 + 3.0, top), (x1, bot + fl), ((x0 + x1) / 2, bot + 4.5 + fl), (x0, bot + fl)]
            sb.wash(cr, poly, awn if s_ % 2 == 0 else P["lead_white"], 0.97, 0.35)
        cr.new_path()
        core.polygon(cr, [(x - 1, top), (x + w + 7, top), (x + w + 4, bot), (x - 4, bot)])
        sb.ink_outline(cr, B.Path(cr), 0.6, INK, 0.8)
        sa = 0.1 * math.sin(t * 1.4 + k * 1.1)
        cr.save()
        cr.translate(x + w * 0.5, top - 15.0)
        cr.rotate(sa)
        sb.ink(cr, [(-12, -6), (-12, 0)], 0.55, INK, 0.9)
        sb.ink(cr, [(12, -6), (12, 0)], 0.55, INK, 0.9)
        board = [(-19, 0), (19, 0), (19, 11), (-19, 11)]
        pb = sb.wash(cr, board, "#c79a62", 0.98, 0.45)
        sb.ink_outline(cr, pb, 0.65, INK, 0.9)
        core.text(cr, sign, 0, 8.4, 7.4, sb.SIGN_FONT, INK, align="center", alpha_=0.92)
        cr.restore()


# ----------------------------------------------------------------------------------------
# verse 1's bas-de-page: potions for sleeping and charms for the rain
# ----------------------------------------------------------------------------------------

class PotionShelf(_Synced):
    """A marginal still life under the first verse: a little oak shelf of potions (a blue sleeping
    draught with a crescent label), a jar of glowing berries, a cold spell-candle, and a rune
    charm hanging from a nail, painted straight onto the parchment."""
    DW, DH = 220.0, 80.0
    grain = 0.0

    def back(self, cr):
        # ivy trailing along the shelf
        vine = [(4, 52), (30, 46), (60, 54), (100, 48), (140, 55), (180, 47), (216, 53)]
        sb.ink(cr, vine, 1.2, P["olive"], 0.8, (0.4, 1.0, 0.4))
        for i, (vx, vy) in enumerate(vine[1:-1]):
            leaf = [(vx, vy), (vx + 4, vy - 5), (vx + 9, vy - 3), (vx + 5, vy + 1)]
            pl = sb.wash(cr, leaf, (P["verdigris"], P["sap"])[i % 2], 0.9, 0.3, smooth_t=0.6)
            sb.ink_outline(cr, pl, 0.4, INK, 0.6)
        # the shelf
        sh = [(20, 58), (200, 58), (198, 64), (22, 64)]
        ps = sb.wash(cr, sh, "#8a5a36", 0.97, 0.45)
        sb.ink_outline(cr, ps, 0.6, INK, 0.85)
        for bx in (40, 180):
            sb.ink(cr, [(bx, 64), (bx - 3, 72)], 1.6, "#6e4a30", 0.9)
        # potions
        self._bottles = []
        for k, (bx, bh, c, lab) in enumerate(((52, 26, P["ultramarine"], True), (78, 20, "#6b4fa0", False),
                                              (104, 24, P["verdigris"], False))):
            by = 57.5
            pts = [(bx - 7, by), (bx - 8, by - bh * 0.55), (bx - 2.6, by - bh * 0.75), (bx - 2.4, by - bh), (bx + 2.4, by - bh),
                   (bx + 2.6, by - bh * 0.75), (bx + 8, by - bh * 0.55), (bx + 7, by)]
            pb = sb.wash(cr, pts, c, 0.9, 0.45, smooth_t=0.35)
            sb.ink_outline(cr, pb, 0.6, INK, 0.85)
            cork = [(bx - 2.6, by - bh), (bx + 2.6, by - bh), (bx + 2.2, by - bh - 4), (bx - 2.2, by - bh - 4)]
            sb.ink_outline(cr, sb.wash(cr, cork, "#b07a48", 0.97, 0.3), 0.4, INK, 0.8)
            if lab:
                lb = [(bx - 5, by - 12), (bx + 5, by - 12), (bx + 5, by - 4), (bx - 5, by - 4)]
                sb.ink_outline(cr, sb.wash(cr, lb, P["bone"], 0.97, 0.3), 0.4, INK, 0.7)
                cm = crescent_pts(bx, by - 8, 2.6, 1.4, -0.8, 2.2)
                sb.wash(cr, cm, P["ultramarine"], 0.95, 0.0)
            self._bottles.append((bx, by - bh * 0.45))
        # a jar of berries
        jx = 132
        jar = [(jx - 8, 57.5), (jx - 8, 40), (jx + 8, 40), (jx + 8, 57.5)]
        pj = sb.wash(cr, jar, "#d6e0dc", 0.7, 0.35)
        for q in range(7):
            cr.new_path()
            core.circle(cr, jx - 5 + (q % 4) * 3.4, 54 - (q // 4) * 3.6 - (q % 2), 1.6)
            core.src(cr, (P["madder"], P["rose"])[q % 2], 0.95)
            cr.fill()
        sb.ink_outline(cr, pj, 0.5, INK, 0.8)
        cl = [(jx - 9, 40), (jx + 9, 40), (jx + 7, 36), (jx - 7, 36)]
        sb.ink_outline(cr, sb.wash(cr, cl, P["bone"], 0.95, 0.3), 0.4, INK, 0.7)
        # a candle in a glass
        cx_ = 160
        sb.ink_outline(cr, sb.wash(cr, [(cx_ - 6, 57.5), (cx_ - 6, 42), (cx_ + 6, 42), (cx_ + 6, 57.5)], "#cfd8e2", 0.6, 0.3),
                       0.45, INK, 0.75)
        sb.wash(cr, [(cx_ - 3.4, 56), (cx_ - 3.4, 44), (cx_ + 3.4, 44), (cx_ + 3.4, 56)], "#d8c8e8", 0.97, 0.25)
        self._candle = (cx_, 44.0)
        # the charm's nail
        cr.new_path()
        core.circle(cr, 186, 10, 1.2)
        core.src(cr, "#3a3633")
        cr.fill()

    def anim(self, cr, t):
        if not hasattr(self, "_bottles"):
            return
        for k, (bx, by) in enumerate(self._bottles):
            g = 0.5 + 0.5 * math.sin(t * 1.3 + k * 2.1)
            if g > 0.7:
                fx.sparkle(cr, bx - 3.0, by - 2.0, 3.0 * (g - 0.7) / 0.3 + 0.8, "#ffffff", 0.8 * (g - 0.7) / 0.3)
        cx_, cy_ = self._candle
        b, sw, st_ = sb.candle_flicker(t, 5)
        soft_glow(cr, cx_, cy_ - 4, 10.0, "#c9b6ff", 0.35 * b)
        fl = [(cx_ - 1.6, cy_), (cx_ + 0.8 * sw, cy_ - 6.0 * st_), (cx_ + 1.6, cy_)]
        cr.new_path()
        core.smooth_closed(cr, fl + [(cx_, cy_ + 0.8)], 0.8)
        core.src(cr, "#e2d6ff", 0.95)
        cr.fill()
        ang = 0.18 * math.sin(t * 1.5)
        ex_, ey_ = 186 + math.sin(ang) * 26.0, 10 + math.cos(ang) * 26.0
        sb.ink(cr, [(186, 10), (ex_, ey_)], 0.5, INK, 0.9)
        st = [(ex_ - 4.6, ey_ + 1), (ex_ - 2.0, ey_ - 1.6), (ex_ + 3.6, ey_ - 0.6), (ex_ + 4.6, ey_ + 4.6), (ex_ - 0.6, ey_ + 7.0),
              (ex_ - 4.8, ey_ + 4.4)]
        soft_glow(cr, ex_, ey_ + 2.6, 9.0, P["rune"], 0.25 + 0.1 * math.sin(t * 2.0))
        ps = sb.wash(cr, st, P["slate"], 0.98, 0.4, smooth_t=0.5)
        sb.ink_outline(cr, ps, 0.5, INK, 0.85)
        sb.ink(cr, [(ex_ - 1.6, ey_ + 1.0), (ex_ + 0.6, ey_ + 3.6), (ex_ + 2.0, ey_ + 0.6)], 0.6, P["rune"], 0.8)


# ----------------------------------------------------------------------------------------
# the last page: the wash-house at night (we push into its middle window, then black -> S1)
# ----------------------------------------------------------------------------------------

class WashHouseNight(_Synced):
    """The tale begins here: the wash-house at night -- grey stone and slate under a cold indigo sky,
    the gold moon, three tall arched windows glowing sickly teal with tumbling drums behind round
    portholes, a hanging WASH-HOUSE board, cold steam from the chimney, a caged wisp-lamp, and the
    dragon himself, small, trudging toward the door with his laundry sack. The camera pushes into
    the middle window as the picture goes to black (S1 opens inside)."""
    DW, DH = 200.0, 287.0
    grain = 0.3
    WIN = ((44.0, 236.0), (100.0, 236.0), (156.0, 236.0))     # window centres (x) and sills (y)

    def back(self, cr):
        sb._sky(cr, self.DW, self.DH, [(0.0, "#0f1430"), (0.35, "#18224a"), (0.7, "#1f3a52"), (1.0, "#2d5058")],
                seed=self.seed + 8, blooms=6, bottom=210)
        sb.gild(cr, crescent_pts(52, 40, 15, 6.5, -4.5, 13.5), outline=0.6, shimmer=0.4)
        self._stars = [(16, 18, 2.4), (90, 14, 1.8), (128, 34, 2.6), (176, 16, 2.0), (186, 70, 1.6), (110, 60, 1.4),
                       (24, 88, 1.6), (150, 92, 1.4)]
        for (sx_, sy_, r) in self._stars:
            gold_star(cr, sx_, sy_, r, shimmer=0.3)
        stipple(cr, 0, 0, self.DW, 120, 40, "#dfe8ff", 0.3, (0.2, 0.45), seed=self.seed + 4)
        # the building
        body = sb.wobble([(10, 268), (10, 150), (190, 150), (190, 268)], 0.6, 2)
        pb = sb.wash(cr, body, "#7a868c", 0.97, 0.45)
        cr.save()
        pb.add(cr)
        cr.clip()
        rng = random.Random(self.seed + 3)
        blocks = []
        for row in range(14):
            y = 152 + row * 8.6
            x = 10 + (row % 2) * 8
            blocks.append([(10, y), (190, y)])
            while x < 190:
                w = rng.uniform(13, 21)
                blocks.append([(x, y), (x, y + 8.6)])
                x += w
        B.detail_lines(cr, blocks, 0.38, INK, 0.3, taper=(1.0, 1.0, 1.0))
        stipple(cr, 10, 150, 190, 268, 120, "#2a3338", 0.25, (0.2, 0.5), seed=12)
        g = core.linear(10, 0, 190, 0, [(0.0, (0.0, 0.0, 0.0, 0.0)), (0.6, (0.0, 0.0, 0.0, 0.0)), (1.0, (0.05, 0.06, 0.1, 0.35))])
        cr.set_source(g)
        cr.paint()
        cr.restore()
        sb.ink_outline(cr, pb, 0.9, INK, 0.9)
        roof = sb.wobble([(0, 152), (100, 92), (200, 152)], 0.6, 4)
        pr = sb.wash(cr, roof, "#3e475c", 0.97, 0.5)
        sb.hatch(cr, pr, 0.55, 2.4, 0.35, INK, 0.3)
        cr.save()
        pr.add(cr)
        cr.clip()
        B.detail_lines(cr, [[(0, y), (200, y)] for y in range(100, 152, 5)], 0.3, INK, 0.3, taper=(1.0, 1.0, 1.0))
        cr.restore()
        sb.ink_outline(cr, pr, 0.9, INK, 0.9)
        chn = [(142, 108), (142, 76), (158, 76), (158, 118)]
        sb.ink_outline(cr, sb.wash(cr, chn, "#5f6672", 0.97, 0.4), 0.8, INK, 0.9)
        # buttresses
        for bx in (66, 130):
            bt = [(bx - 4, 268), (bx - 3, 160), (bx + 3, 160), (bx + 4, 268)]
            sb.ink_outline(cr, sb.wash(cr, bt, "#6c777e", 0.97, 0.35), 0.6, INK, 0.8)
        # the window openings (filled per frame), deep reveals
        self._wins = []
        for (wx, sill) in self.WIN:
            ww, wh = 30.0, 66.0
            arch = _door_arch(wx - ww * 0.5, sill - wh, ww, wh, n=10)
            outer = _door_arch(wx - ww * 0.5 - 3.0, sill - wh - 3.0, ww + 6.0, wh + 3.0, n=10)
            sb.ink_outline(cr, sb.wash(cr, outer, "#5a646c", 0.97, 0.3), 0.6, INK, 0.85)
            self._wins.append((wx, sill, ww, wh, arch))
            sb.wash(cr, [(wx - ww * 0.5 - 4, sill), (wx + ww * 0.5 + 4, sill), (wx + ww * 0.5 + 5, sill + 3),
                         (wx - ww * 0.5 - 5, sill + 3)], "#6c777e", 0.97, 0.3)
        # the door at the right end, under its caged wisp-lamp
        door = _door_arch(171.0, 236.0, 15.0, 32.0, n=8)
        sb.ink_outline(cr, sb.wash(cr, _door_arch(168.0, 233.0, 21.0, 35.0, n=8), "#5a646c", 0.97, 0.3), 0.6, INK, 0.85)
        pin = sb.wash(cr, door, "#163c3c", 0.99, 0.3)            # the doorway: the cold-lit wash-house inside
        cr.save()
        pin.add(cr)
        cr.clip()
        soft_glow(cr, 178.5, 256.0, 22.0, P["wisp"], 0.45)
        cr.restore()
        self._door = door
        sb.wash(cr, [(166.0, 268.0), (192.0, 268.0), (194.0, 271.0), (164.0, 271.0)], "#6c777e", 0.97, 0.3)
        # cobbles
        street = [(-6, 266), (206, 266), (206, self.DH + 4), (-6, self.DH + 4)]
        ps = sb.wash(cr, street, "#55616a", 0.97, 0.3)
        cr.save()
        ps.add(cr)
        cr.clip()
        arcs = []
        yy = 268.0
        row = 0
        while yy < self.DH + 4:
            xx = -8.0 - (row % 2) * 4.0
            while xx < 210:
                w_ = rng.uniform(7.0, 10.0)
                arcs.append([(xx + 0.8, yy + 2.0), (xx + w_ * 0.5, yy - 0.4), (xx + w_ - 0.8, yy + 2.0)])
                xx += w_
            yy += 4.0
            row += 1
        B.detail_lines(cr, arcs, 0.4, INK, 0.4)
        cr.restore()

    def anim(self, cr, t):
        if not hasattr(self, "_wins"):
            return
        for i, (sx_, sy_, r) in enumerate(self._stars):
            a = 0.5 + 0.5 * math.sin(t * (1.2 + 0.3 * (i % 4)) + i * 2.1)
            if a > 0.65:
                fx.sparkle(cr, sx_, sy_, r * 1.8 * a, "#e8f0ff", 0.5 * (a - 0.65) / 0.35 + 0.1)
        for k, (wx, sill, ww, wh, arch) in enumerate(self._wins):
            pulse = 0.78 + 0.22 * math.sin(t * 2.2 + k * 1.3) + 0.06 * math.sin(t * 13.0 + k)
            pw = sb.wash(cr, arch, core.mix("#10302f", P["teal"], 0.62 * pulse), 0.98, 0.3)
            cr.save()
            pw.add(cr)
            cr.clip()
            soft_glow(cr, wx, sill - wh * 0.4, 34.0, P["wisp"], 0.3 * pulse)
            # leading
            lines = [[(wx, sill - wh), (wx, sill)]] + [[(wx - ww, sill - wh * q), (wx + ww, sill - wh * q)] for q in (0.3, 0.62)]
            B.detail_lines(cr, lines, 0.5, "#14201f", 0.75, taper=(1.0, 1.0, 1.0))
            # a drum's porthole behind the glass, its laundry tumbling
            cx, cy, r = wx, sill - wh * 0.36, ww * 0.3
            cr.new_path()
            core.circle(cr, cx, cy, r + 2.2)
            core.src(cr, "#b49248", 0.97)
            cr.fill()
            cr.new_path()
            core.circle(cr, cx, cy, r)
            core.src(cr, "#0d2526", 0.97)
            cr.fill()
            ang = t * 2.4 + k * 1.7
            for j, c in enumerate((P["vermilion"], P["azure"], P["bone"], P["ochre"])):
                a = ang + j * 1.6
                cr.new_path()
                core.ellipse(cr, cx + math.cos(a) * r * 0.42, cy + math.sin(a) * r * 0.42 + 0.5, r * 0.36, r * 0.24, a)
                core.src(cr, c, 0.88)
                cr.fill()
            fx.sparkle(cr, cx - r * 0.45, cy - r * 0.45, r * 0.3, "#d8fff6", 0.55)
            cr.restore()
            sb.ink_outline(cr, pw, 0.9, INK, 0.9)
        # the hanging board
        sa = 0.06 * math.sin(t * 1.1)
        cr.save()
        cr.translate(100, 160)
        cr.rotate(sa)
        board = [(-36, 0), (36, 0), (36, 14), (-36, 14)]
        sb.ink(cr, [(-28, -6), (-28, 0)], 0.6, INK, 0.9)
        sb.ink(cr, [(28, -6), (28, 0)], 0.6, INK, 0.9)
        sb.ink_outline(cr, sb.wash(cr, board, "#6e5034", 0.98, 0.45), 0.7, INK, 0.9)
        core.text(cr, "WASH-HOUSE", 0, 10.4, 9.0, sb.SIGN_FONT, P["gold_hi"], align="center", alpha_=0.95)
        cr.restore()
        # cold steam from the chimney
        for j in range(5):
            u = (t * 0.2 + j * 0.2) % 1.0
            cr.new_path()
            core.circle(cr, 150 + 6.0 * math.sin(u * 4 + j) + u * 12, 72 - u * 50, 4.0 + u * 7.0)
            core.src(cr, "#b8ccd2", 0.24 * (1 - u))
            cr.fill()
        # the caged wisp-lamp by the door
        sb._lantern(cr, 196, 226, t, phase=0.3, scale=0.9, warm=False)
        # the dragon, small, trudging to the door with his laundry sack. Constant pace, then a short
        # slow-down at the door (the walk phase comes from the distance actually travelled, so his
        # feet never skate); the door swings open spilling cold wisp-light on him and he steps inside
        # as the picture goes dark -- S1 opens in there.
        e = self.e
        t0, t1 = e("wash_walk", 0.0), e("wash_door", 9.0)
        x0, x1 = 64.0, 163.0
        u = clamp((t - t0) / max(0.1, t1 - t0))
        k = 0.82                                   # constant pace until here, then ease into the stop
        if u < k:
            prog = u / (k + 0.5 * (1.0 - k))
        else:
            w = (u - k) / (1.0 - k)
            prog = (k + (1.0 - k) * (w - 0.5 * w * w)) / (k + 0.5 * (1.0 - k))
        x = lerp(x0, x1, prog)
        walk = 1.0 - smooth((u - 0.9) / 0.1)
        # the door: opens over 0.45 s from his arrival; he takes one step into its light (the picture
        # is going black by then: S1 finds him inside)
        opn = smooth((t - t1) / 0.45)
        step = clamp((t - (t1 + 0.3)) / 0.6)
        if step > 0.0:
            x = lerp(x1, 171.0, core.inout_sine(step))
            walk = math.sin(math.pi * step)
        alpha = 0.95
        dist = x - x0
        if opn > 0.01:
            # the cold light spilling out across the cobbles (and onto him)
            soft_glow(cr, 179.0, 270.0, 26.0 * opn, P["wisp"], 0.35 * opn)
        self._draw_door_leaf(cr, opn)
        if alpha > 0.01:
            pose = ch.DragonPose(facing=1, walk=walk, phase=ch.dragon_walk_phase(dist, 0.12, 1), mood="tired",
                                 wings=-0.8, hunch=0.8, tail_drag=0.3, seed=5,
                                 head_turn=0.25 * smooth((u - 0.85) / 0.15) * (1.0 - opn),
                                 far=ch.Arm("carry_bag", hold=lambda c, f: self._sack(c, f)))
            storybook_dragon_posed(cr, x, 284.0, 0.12, t, pose, alpha=alpha, tint=0.18)
            if opn > 0.01:
                soft_glow(cr, x + 6.0, 262.0, 18.0, P["wisp"], 0.18 * opn * alpha)

    def _draw_door_leaf(self, cr, opn):
        """The oak door leaf on its left hinge: shut it covers the doorway; it swings inward (narrowing
        toward the hinge, darkening as it turns away from the moon)."""
        dx, dy, dw, dh = 171.0, 236.0, 15.0, 32.0
        k = 1.0 - 0.86 * clamp(opn)
        if k <= 0.02:
            return
        cr.save()
        cr.new_path()
        core.polygon(cr, self._door)
        cr.clip()
        cr.translate(dx, 0.0)
        cr.scale(k, 1.0)
        cr.translate(-dx, 0.0)
        leaf = [(dx, dy - 2.0), (dx + dw, dy - 2.0), (dx + dw, dy + dh), (dx, dy + dh)]
        pl = sb.wash(cr, leaf, core.mix("#3c2a1c", "#1e140e", 0.6 * clamp(opn)), 0.99, 0.3)
        B.detail_lines(cr, [[(dx + dw * j / 3.0, dy + 2.0), (dx + dw * j / 3.0, dy + dh)] for j in (1, 2)], 0.4, INK, 0.5,
                       taper=(1.0, 1.0, 1.0))
        B.detail_lines(cr, [[(dx + 0.5, dy + dh * 0.35), (dx + dw * 0.7, dy + dh * 0.35)],
                            [(dx + 0.5, dy + dh * 0.78), (dx + dw * 0.7, dy + dh * 0.78)]], 0.8, "#2b2522", 0.95,
                       taper=(1.0, 1.0, 1.0))
        cr.new_path()
        core.circle(cr, dx + dw * 0.8, dy + dh * 0.56, 0.9)
        core.src(cr, "#b49248", 0.95)
        cr.fill()
        sb.ink_outline(cr, pl, 0.5, INK, 0.85)
        cr.restore()
        sb.ink_outline(cr, _poly(cr, self._door), 0.7, INK, 0.9)

    @staticmethod
    def _sack(cr, f):
        """His laundry: a lumpy linen sack hanging plumb from his fist (hold units are px at the
        holder's scale 1.0, so this is sized for a full-size dragon), a sleeve poking out of the
        gathered neck."""
        cr.save()
        cr.rotate(-f.angle)
        k = 4.2
        neck = [(-9 * k, -2 * k), (9 * k, -2 * k), (6 * k, 6 * k), (-6 * k, 6 * k)]
        sack = [(-8 * k, 4 * k), (8 * k, 4 * k), (19 * k, 22 * k), (17 * k, 34 * k), (4 * k, 39 * k), (-12 * k, 37 * k),
                (-19 * k, 26 * k)]
        p = sb.wash(cr, sack, "#d8cdb6", 0.98, 0.4, smooth_t=0.6)
        sb.wash(cr, [(2 * k, 10 * k), (17 * k, 24 * k), (14 * k, 34 * k), (3 * k, 37 * k)], "#b7aa90", 0.6, 0.0, smooth_t=0.6)
        sb.ink_outline(cr, p, 1.4 * k, INK, 0.9)
        sleeve = [(-2 * k, -1 * k), (5 * k, -6 * k), (10 * k, -4 * k), (4 * k, 3 * k)]
        sb.ink_outline(cr, sb.wash(cr, sleeve, "#9a6b8c", 0.98, 0.3, smooth_t=0.5), 1.2 * k, INK, 0.85)
        sb.ink_outline(cr, sb.wash(cr, neck, "#cbbf9f", 0.98, 0.3), 1.2 * k, INK, 0.9)
        cr.restore()


# ----------------------------------------------------------------------------------------
# the verse, written onto the page by an invisible quill as it is sung
# ----------------------------------------------------------------------------------------

_FONT_OPTS = None


def _font_opts():
    global _FONT_OPTS
    if _FONT_OPTS is None:
        fo = cairo.FontOptions()
        fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
        fo.set_hint_style(cairo.HINT_STYLE_NONE)
        fo.set_antialias(cairo.ANTIALIAS_GRAY)
        _FONT_OPTS = fo
    return _FONT_OPTS


def _timed_words(text, lids, skip_first_letter=False):
    """Assign song word times to the words of `text` (the page's lines, '\\n'-separated, '>' =
    indented half-line) by walking the sung words of lines `lids` in order."""
    sung = []
    for lid in lids:
        sung += SONG.words(lid)
    out, k = [], 0
    for para in text.split("\n"):
        ind = para.startswith(">")
        body = para[1:].lstrip() if ind else para
        words = []
        for w in body.split(" "):
            if not w:
                continue
            if k < len(sung):
                _, a, b = sung[k]
                k += 1
            else:
                a, b = 1e9, 1e9
            words.append((w, a, b))
        out.append((ind, words))
    return out


class VerseText:
    """A block of verse in IM FELL italic, laid out like storybook._page_over (same box, size,
    leading, drop-cap indent, half-line indent), whose words are WRITTEN IN as they are sung: each
    word is wiped on left to right by an invisible quill (a soft edge, a gold fleck at the nib),
    in fresh ink that glows faintly gold and settles to sepia."""

    def __init__(self, text, lids, text_box, size, cap_lines=0, align="left", ink=INK, lead=0.06):
        self.lines = _timed_words(text, lids)
        self.box = text_box
        self.size = size
        self.cap_lines = cap_lines
        self.align = align
        self.ink = core.col(ink)
        self.lead = lead
        self._layout = None

    def _make_layout(self, cr, w, h):
        tx, ty, tw = self.box[0] * w, self.box[1] * h, self.box[2] * w
        size = self.size
        lh = size * 1.24
        cap = lh * self.cap_lines - size * 0.15 if self.cap_lines else 0.0
        core.set_font(cr, size, sb.TEXT_FONT, False, True)
        cr.set_font_options(_font_opts())
        asc = cr.font_extents()[0]
        space = cr.text_extents(" ")[4]
        lay = []
        for i, (ind, words) in enumerate(self.lines):
            widths = [cr.text_extents(wd)[4] for wd, _, _ in words]
            total = sum(widths) + space * max(0, len(words) - 1)
            if self.align == "center":
                x = tx + tw / 2.0 - total / 2.0
            else:
                x = tx + (cap + size * 0.5 if i < self.cap_lines else (size * 1.3 if ind else 0.0))
            y = ty + asc + i * lh
            items = []
            for (wd, a, b), ww in zip(words, widths):
                items.append((wd, x, ww, a, b))
                x += ww + space
            lay.append((y, items))
        self._layout = (w, h, lay)

    def done(self, t):
        """True when every word has been written."""
        return all(b <= t for _, words in self.lines for _, a, b in words)

    def draw(self, cr, w, h, t, alpha=1.0):
        cr.save()
        core.set_font(cr, self.size, sb.TEXT_FONT, False, True)
        cr.set_font_options(_font_opts())
        if self._layout is None or self._layout[0] != w or self._layout[1] != h:
            self._make_layout(cr, w, h)
        ink = self.ink
        gold = core.col(P["gold_dk"])
        soft = self.size * 0.55
        for y, items in self._layout[2]:
            for (wd, x, ww, a, b) in items:
                t0 = a - self.lead
                if t < t0:
                    continue
                dur = clamp((b - a) * 0.8, 0.14, 0.42)
                u = clamp((t - t0) / dur)
                age = t - (t0 + dur)
                settle = smooth(clamp(age / 0.9)) if age > 0 else 0.0
                c = core.mix(gold, ink, 0.35 + 0.65 * settle)
                al = 0.93 * alpha
                if u >= 1.0:
                    core.src(cr, c, al)
                    cr.move_to(x, y)
                    cr.show_text(wd)
                    continue
                # the word being written: clip to its glyphs, wipe a soft ink edge across it
                cr.save()
                cr.move_to(x, y)
                cr.text_path(wd)
                cr.clip()
                front = x + (ww + soft) * u
                g = cairo.LinearGradient(front - soft, 0, front, 0)
                g.add_color_stop_rgba(0.0, c[0], c[1], c[2], al)
                g.add_color_stop_rgba(1.0, c[0], c[1], c[2], 0.0)
                cr.set_source(g)
                cr.paint()
                cr.restore()
                # the nib: a fleck of gold where the quill is
                fx.sparkle(cr, min(x + ww, front - soft * 0.5), y - self.size * 0.32, self.size * 0.28,
                           P["gold_hi"], 0.85 * alpha * math.sin(math.pi * u))
        cr.restore()


# ----------------------------------------------------------------------------------------
# Kells illumination: a lapis border with a twisted gold cord, vermilion corner panels with gilt
# triskeles, and the Insular manuscripts' rows of red dots round frames and initials
# ----------------------------------------------------------------------------------------

LAPIS = "#2b4687"
KELLS_BAND = (9.4, 13.0)                    # the border band, page units in from the edge


def red_dots_along(cr, pts, step=1.7, off=1.4, r=0.34, color=None, alpha=0.85, closed=True):
    """The Insular red-dot contour: dots spaced `step` apart, `off` outside the polyline pts
    (outside = to the left of travel for a clockwise loop in y-down space)."""
    color = color or P["vermilion"]
    seq = pts + ([pts[0]] if closed and pts[0] != pts[-1] else [])
    acc = 0.0
    nxt = 0.0
    cr.new_path()
    for (x0, y0), (x1, y1) in zip(seq, seq[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1e-6:
            continue
        nx, ny = (y1 - y0) / L, -(x1 - x0) / L
        while nxt <= acc + L:
            u = (nxt - acc) / L
            px_, py_ = x0 + (x1 - x0) * u + nx * off, y0 + (y1 - y0) * u + ny * off
            cr.new_sub_path()
            cr.arc(px_, py_, r, 0, TAU)
            nxt += step
        acc += L
    core.src(cr, color, alpha)
    cr.fill()


def _triskele(cr, cx, cy, r, color, w):
    arms = []
    for k in range(3):
        a0 = k * TAU / 3.0
        ex, ey = cx + math.cos(a0) * r * 0.55, cy + math.sin(a0) * r * 0.55
        arms.append(spiral_pts(ex, ey, r * 0.05, r * 0.45, turns=1.25, n=16, a0=a0 + math.pi, cw=1))
    B.detail_lines(cr, arms, w, color, 0.95, taper=(0.4, 1.0, 0.7))


def kells_border(cr, w, h, side=1, seed=0, shimmer=0.5, gutter_boss=True):
    """The page's illuminated border band (static: cache it): lapis between gold rules, a twisted
    gold cord running round it, vermilion corner panels with gilt triskeles, a gilded boss at the
    middle of the fore-edge side, and red dots along the outside."""
    m0, m1 = KELLS_BAND
    bwid = m1 - m0
    outer = [(m0, m0), (w - m0, m0), (w - m0, h - m0), (m0, h - m0)]
    inner = [(m1, m1), (w - m1, m1), (w - m1, h - m1), (m1, h - m1)]
    cr.save()
    cr.new_path()
    core.polygon(cr, outer)
    core.polygon(cr, inner[::-1])
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    band = B.Path(cr)
    band.add(cr)
    core.src(cr, LAPIS, 0.96)
    cr.fill()
    # the cord: diagonal gold strokes, each with a dark lower edge (the twist)
    cr.save()
    band.add(cr)
    cr.clip()
    strokes, shadows = [], []
    pitch = 2.0

    def side_run(x0, y0, x1, y1, nx, ny):
        L = math.hypot(x1 - x0, y1 - y0)
        tx, ty = (x1 - x0) / L, (y1 - y0) / L
        n = int(L / pitch) + 2
        for k in range(-1, n):
            s0 = k * pitch
            a = (x0 + tx * s0 + nx * 0.5, y0 + ty * s0 + ny * 0.5)
            b = (x0 + tx * (s0 + pitch * 1.25) + nx * (bwid - 0.5), y0 + ty * (s0 + pitch * 1.25) + ny * (bwid - 0.5))
            mid = ((a[0] + b[0]) * 0.5 - tx * 0.25, (a[1] + b[1]) * 0.5 - ty * 0.25)
            strokes.append([a, mid, b])
            shadows.append([(a[0] + tx * 0.55, a[1] + ty * 0.55), (mid[0] + tx * 0.55, mid[1] + ty * 0.55),
                            (b[0] + tx * 0.55, b[1] + ty * 0.55)])
    side_run(m0, m0, w - m0, m0, 0.0, 1.0)
    side_run(w - m0, m0, w - m0, h - m0, -1.0, 0.0)
    side_run(w - m0, h - m0, m0, h - m0, 0.0, -1.0)
    side_run(m0, h - m0, m0, m0, 1.0, 0.0)
    B.detail_lines(cr, shadows, 0.62, "#14204a", 0.85, taper=(0.3, 1.0, 0.3))
    B.detail_lines(cr, strokes, 0.72, P["gold"], 0.95, taper=(0.3, 1.0, 0.3))
    B.detail_lines(cr, strokes, 0.22, P["gold_hi"], 0.7, taper=(0.2, 1.0, 0.2))
    cr.restore()
    # the gold rules
    for poly, lw in ((outer, 0.55), (inner, 0.55)):
        cr.new_path()
        core.polygon(cr, poly)
        cr.close_path()
        cr.set_line_width(lw)
        core.src(cr, P["gold"], 1.0)
        cr.stroke()
    for poly in ([(m0 - 0.45, m0 - 0.45), (w - m0 + 0.45, m0 - 0.45), (w - m0 + 0.45, h - m0 + 0.45), (m0 - 0.45, h - m0 + 0.45)],
                 [(m1 + 0.45, m1 + 0.45), (w - m1 - 0.45, m1 + 0.45), (w - m1 - 0.45, h - m1 - 0.45), (m1 + 0.45, h - m1 - 0.45)]):
        cr.new_path()
        core.polygon(cr, poly)
        cr.close_path()
        cr.set_line_width(0.22)
        core.src(cr, INK, 0.75)
        cr.stroke()
    cr.restore()
    # corner panels: vermilion squares, gilt edge, a gold triskele
    cs = bwid + 2.4
    for (cx, cy) in ((m0 + bwid * 0.5, m0 + bwid * 0.5), (w - m0 - bwid * 0.5, m0 + bwid * 0.5),
                     (w - m0 - bwid * 0.5, h - m0 - bwid * 0.5), (m0 + bwid * 0.5, h - m0 - bwid * 0.5)):
        sq = [(cx - cs * 0.5, cy - cs * 0.5), (cx + cs * 0.5, cy - cs * 0.5), (cx + cs * 0.5, cy + cs * 0.5),
              (cx - cs * 0.5, cy + cs * 0.5)]
        cr.new_path()
        core.polygon(cr, sq)
        sp_ = B.Path(cr)
        sp_.add(cr)
        core.src(cr, P["vermilion"], 0.98)
        cr.fill()
        sp_.add(cr)
        cr.set_line_width(0.7)
        core.src(cr, P["gold"], 1.0)
        cr.stroke()
        sb.ink_outline(cr, sp_, 0.22, INK, 0.8)
        _triskele(cr, cx, cy, cs * 0.42, P["gold_hi"], 0.42)
        red_dots_along(cr, sq, step=1.5, off=1.0, r=0.3)
    # a gilded boss at the middle of the fore-edge band, and two small ones on the head and tail
    ox = m0 + bwid * 0.5 if side < 0 else w - m0 - bwid * 0.5
    for (bx_, by_, r_) in ((ox, h * 0.5, bwid * 0.75), (w * 0.5, m0 + bwid * 0.5, bwid * 0.5),
                           (w * 0.5, h - m0 - bwid * 0.5, bwid * 0.5)):
        cr.new_path()
        core.circle(cr, bx_, by_, r_)
        sb.gild(cr, path=B.Path(cr), shimmer=shimmer, outline=0.25)
        cr.new_path()
        core.circle(cr, bx_, by_, r_ * 0.42)
        core.src(cr, P["vermilion"], 0.95)
        cr.fill()
    # red dots along the outside of the band
    red_dots_along(cr, [(m0, m0), (w - m0, m0), (w - m0, h - m0), (m0, h - m0)], step=1.75, off=-1.25, r=0.32)


ORN_MAX_BUCKET = 16.0


class PageArt:
    """One page's living content, used as the Page's `illus` over the whole page (box (0,0,1,1),
    frame None): its illustration clipped to a gilt frame + the verse being written. Because it is
    part of the page itself, it turns with the page. Its illumination (the Kells border band, the
    red-dot contours round the frame and the initial) is static, cached per resolution bucket and
    painted over the picture."""

    def __init__(self, illus=None, box=None, frame="arch", verse=None, side=1, border=True, cap=None, seed=0):
        self.illus = illus
        self.box = box
        self.frame = frame
        self.verse = verse
        self.side = side
        self.border = border
        self.cap = cap                      # (x, y, size) of the library's drop cap, page units
        self.seed = seed
        self._orn = {}

    def _ornament(self, cr, w, h):
        dev = B.device_scale(cr)
        bucket = min(ORN_MAX_BUCKET, 2.0 ** (math.ceil(math.log2(max(0.25, dev)) * 2.0) / 2.0))
        key = (round(w, 2), round(h, 2), bucket)
        surf = self._orn.get(key)
        if surf is None:
            if len(self._orn) > 3:
                self._orn.clear()
            surf = core.new_surface(max(1, int(math.ceil(w * bucket))), max(1, int(math.ceil(h * bucket))))
            c2 = core.new_context(surf)
            c2.scale(bucket, bucket)
            if self.border:
                kells_border(c2, w, h, self.side, self.seed)
            if self.illus is not None and self.box is not None and self.frame:
                bx, by, bw, bh = self.box[0] * w, self.box[1] * h, self.box[2] * w, self.box[3] * h
                pts = _flat_pts(lambda c: sb._frame_path(c, bx - 2.2, by - 2.2, bw + 4.4, bh + 2.2, self.frame))
                red_dots_along(c2, pts, step=1.6, off=0.0, r=0.32)
            if self.cap is not None:
                x_, y_, s_ = self.cap
                red_dots_along(c2, [(x_ - 1.6, y_ - 1.6), (x_ + s_ + 1.6, y_ - 1.6), (x_ + s_ + 1.6, y_ + s_ + 1.6),
                                    (x_ - 1.6, y_ + s_ + 1.6)], step=1.5, off=0.0, r=0.3)
            surf.flush()
            self._orn[key] = surf
        return surf, bucket

    def __call__(self, cr, w, h, t=0.0):
        if self.illus is not None and self.box is not None:
            bx, by, bw, bh = self.box[0] * w, self.box[1] * h, self.box[2] * w, self.box[3] * h
            if self.frame:
                fp = sb._frame_path(cr, bx, by, bw, bh, self.frame)
                cr.save()
                fp.add(cr)
                cr.clip()
                cr.translate(bx, by)
                self.illus(cr, bw, bh, t)
                cr.restore()
                # the gilt frame: a broad gold moulding, a lapis fillet inside it, ink both sides
                cr.save()
                fp.add(cr)
                cr.set_line_width(w * 0.022)
                cr.set_source_rgb(*core.col(P["gold"])[:3])
                cr.stroke()
                fp.add(cr)
                cr.set_line_width(w * 0.006)
                cr.set_source_rgb(*core.col(LAPIS)[:3])
                cr.stroke()
                cr.restore()
                sb.ink_outline(cr, fp, w * 0.0035, INK, 0.85)
            else:
                cr.save()
                cr.translate(bx, by)
                self.illus(cr, bw, bh, t)
                cr.restore()
        if self.border or (self.frame and self.box is not None) or self.cap is not None:
            surf, bucket = self._ornament(cr, w, h)
            cr.save()
            cr.scale(1.0 / bucket, 1.0 / bucket)
            cr.set_source_surface(surf, 0, 0)
            cr.get_source().set_filter(cairo.FILTER_BILINEAR)
            cr.paint()
            cr.restore()
        if self.verse is not None:
            self.verse.draw(cr, w, h, t)


def _flat_pts(build):
    """Flatten a path built by build(cr) into a polyline."""
    surf, c = core.frame(4, 4)
    c.new_path()
    res = build(c)
    if res is not None and hasattr(res, "add"):
        c.new_path()
        res.add(c)
    pts = []
    for kind, xy in c.copy_path_flat():
        if kind in (cairo.PATH_MOVE_TO, cairo.PATH_LINE_TO) and xy:
            pts.append(tuple(xy))
    return pts


# ----------------------------------------------------------------------------------------
# the book
# ----------------------------------------------------------------------------------------

V1_TEXT = ("nce upon a time,\n>in a kingdom of stone,\nLived a town full of folk\n>who were living alone.\n"
           "They had potions for sleeping\n>and charms for the rain,\nAnd a lock on each heart,\n"
           ">and a latch on each pane.")
V2A_TEXT = "Now a dragon lived there\nwith a scarf and a sigh,\nAnd he waved at his neighbours,\nwho hurried on by."
V2B_TEXT = "Every merchant in town\nhad a stone he could sell —\nBut for what he was missing,\nthere wasn’t a spell."
CODA_TEXT = ("o pull up a stool, friend,\n>and hear how it’s said:\nHow a kingdom of stone\n"
             ">found its way back to bread.")

BOX_TALL = (0.1, 0.07, 0.8, 0.86)          # 120 x 172 page units: DW 200 x DH 287
BOX_V2 = (0.12, 0.31, 0.76, 0.6)            # 114 x 120: DW 200 x DH 212 (the verse sits above it)
TEXT_V2 = (0.12, 0.085, 0.76, 0.2)          # verse 2 is written at the TOP of its page: deep shots keep the
                                            # caption band (bottom of frame) clear of page lettering


def make_book(ev):
    """The prologue's book: 4 spreads with this film's living pages. ev = event times (scene s)."""
    castle = CastleTown(ev, seed=1)
    shelf = PotionShelf(ev, seed=4)
    dragon = DragonStreet(ev, seed=3)
    market = Market(ev, seed=4)
    wash_ = WashHouseNight(ev, seed=5)
    v1 = VerseText(V1_TEXT, ["s0_l1", "s0_l2", "s0_l3", "s0_l4"], (0.11, 0.11, 0.79, 0.5), 150.0 / 17.0, cap_lines=3)
    v2a = VerseText(V2A_TEXT, ["s0_l5", "s0_l6"], TEXT_V2, 150.0 / 18.5, align="center")
    v2b = VerseText(V2B_TEXT, ["s0_l7", "s0_l8"], TEXT_V2, 150.0 / 18.5, align="center")
    coda = VerseText(CODA_TEXT, ["s0_l9", "s0_l10"], (0.11, 0.14, 0.79, 0.3), 150.0 / 17.0, cap_lines=2)
    full = (0.0, 0.0, 1.0, 1.0)
    # the library's drop caps sit at the text box corner: (x, y + size*0.12), size = cap_lines*1.24*size - 0.15*size
    s1 = 150.0 / 17.0
    cap_o = (0.11 * 150.0, 0.11 * 200.0 + s1 * 0.12, 1.24 * s1 * 3 - 0.15 * s1)
    cap_s = (0.11 * 150.0, 0.14 * 200.0 + s1 * 0.12, 1.24 * s1 * 2 - 0.15 * s1)
    spreads = [
        sb.Spread(sb.Page(text=" ", drop_cap="O", text_box=(0.11, 0.11, 0.79, 0.5), text_size=s1, border=None,
                          illus=PageArt(shelf, (0.12, 0.655, 0.76, 0.27), None, v1, side=-1, cap=cap_o, seed=1),
                          box=full, frame=None, folio="j", seed=1),
                  sb.Page(illus=PageArt(castle, BOX_TALL, "gothic", side=1, seed=2), box=full, frame=None, folio="ij",
                          seed=2, border=None)),
        sb.Spread(sb.Page(illus=PageArt(dragon, BOX_V2, "arch", v2a, side=-1, seed=3), box=full, frame=None, folio="iij",
                          seed=3, border=None),
                  sb.Page(illus=PageArt(market, BOX_V2, "arch", v2b, side=1, seed=4), box=full, frame=None, folio="iv",
                          seed=4, border=None)),
        sb.Spread(sb.Page(text=" ", drop_cap="S", cap_lines=2, text_box=(0.11, 0.14, 0.79, 0.3), text_size=s1,
                          illus=PageArt(sb.illus_stool, (0.1, 0.5, 0.8, 0.36), None, coda, side=-1, cap=cap_s, seed=5),
                          box=full, frame=None, folio="v", seed=5, border=None),
                  sb.Page(illus=PageArt(sb.illus_bread, (0.13, 0.09, 0.74, 0.82), "gothic", side=1, seed=6), box=full,
                          frame=None, folio="vj", seed=6, border=None)),
        sb.Spread(sb.Page(text="Here beginneth\nthe tale of\nthe Stone\nand the Bread", align="center", ink=sb.RUBRIC,
                          text_box=(0.12, 0.32, 0.76, 0.3), text_size=150.0 / 13.0,
                          illus=PageArt(sb.illus_fleuron, (0.3, 0.6, 0.4, 0.1), None, side=-1, seed=7),
                          box=full, frame=None, folio="vij", seed=7, border=None),
                  sb.Page(illus=PageArt(wash_, BOX_TALL, "gothic", side=1, seed=8), box=full, frame=None, folio="viij",
                          seed=8, border=None)),
    ]
    book = sb.Book(spreads=spreads)
    book.art = {"castle": castle, "shelf": shelf, "dragon": dragon, "market": market, "wash": wash_,
                "v1": v1, "v2a": v2a, "v2b": v2b, "coda": coda}
    return book
