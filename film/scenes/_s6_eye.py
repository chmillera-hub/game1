"""_s6_eye.py -- scene 6's eye for the dragon's big close-ups (shots D and E, zoom 4-5).

A scene-private copy of film/lib/characters/base.eye with two changes; only s6_bench.draw_dragon
uses it (it swaps it in for the duration of one ch.draw_dragon call):

  * no lid-skin fill: above the lash line the head's own scales show, so a closing lid is never
    a flat, untextured patch from eye to brow, and the far eye's socket never shows as a flat
    dome over the sky (s6_bench also clips the far eye to the head's silhouette);
  * the eyeball's clip polygon never inverts at the corners. In base.eye the upper-lid curve
    drops below the lower lid near the corners once the lid is past half-closed (looking down,
    blinking); the sclera, iris and lid-shadow paint then show in thin slivers along the socket
    edge -- hidden in the library by the lid fill, but "antennae" at the eye corners without it.

The lash line, the lower lid line, the closed-eye arc, the catchlights, the crease and the bags
are exactly base.eye's, so the open eye is unchanged.

eye_far() is the FAR eye in 3/4: the dragon's far eye sits on (or, turned further, wholly past)
the head's contour -- a cartoon far-eye bulge. There the lid IS the silhouette: where the socket
lies outside the head it is drawn as a lid of his scales with an ink contour that runs into the
head's outline, so a blink closes the lid over the bulge (the bulge stays, outlined), never a
flat unoutlined dome or a lid line floating on the sky. Inside the head the face shows as is.
"""

import math

import cairocffi as cairo

from film.lib import core
from film.lib.characters.base import Mat, Path, detail_line, palette

clamp = core.clamp


def eye(cr, cx, cy, rx, ry, light, lw=2.2, *, angle=0.0, look=(0.0, 0.0), lid=0.22, lid_bot=0.06,
        tilt=0.0, outer=1.0, blink=0.0, squint_arc=0.0, iris="#D99A2B", iris_hi=None, pupil="#1d120c",
        pupil_size=0.5, pupil_aspect=1.0, sclera="#F3EEE4", skin="#3E6E73", iris_size=0.66,
        foreshort=1.0, crease=0.35, bags=0.0, lash=1.0, lash_flick=0.0, highlight=1.0, line=None,
        lid_shade=0.12, pupil_scale=1.0, hide_lid=True):
    """base.eye's signature; the lid skin is never filled (hide_lid is ignored)."""
    sk = palette(light, Mat.of(skin, sss=0.2))
    line_c = line if line is not None else sk.line
    lid = clamp(lid + 0.28 * max(0.0, look[1]) - 0.10 * max(0.0, -look[1]))
    closed = clamp(max(lid, blink))
    cr.save()
    cr.translate(cx, cy)
    if angle:
        cr.rotate(angle)
    cr.scale(foreshort * outer, 1.0)     # local x: + toward the outer corner
    n = 9
    xs = [-rx + 2 * rx * i / (n - 1) for i in range(n)]

    def y_eye(x, top):
        k = max(0.0, 1.0 - (x / rx) ** 2)
        return (-1 if top else 1) * ry * math.sqrt(k)

    def y_top(x):
        u = x / rx
        base = -ry + 2.0 * ry * closed
        arch = -0.38 * ry * (1.0 - u * u) * (1.0 - closed * 0.85)
        sl = tilt * 0.42 * ry * u * (1.0 - closed * 0.4)
        return max(y_eye(x, True), base + arch + sl)

    def y_bot(x):
        u = x / rx
        base = ry - 2.0 * ry * lid_bot
        arch = 0.32 * ry * (1.0 - u * u) * (1.0 - lid_bot)
        return min(y_eye(x, False), base + arch)

    top = [(x, y_top(x)) for x in xs]
    bot = [(x, y_bot(x)) for x in xs]
    visible = closed < 0.97 and any(b[1] - a[1] > 0.6 for a, b in zip(top, bot))
    cr.new_path()
    core.ellipse(cr, 0, 0, rx, ry)
    sock = Path(cr)

    def below_top():
        # the region under the upper lid's line (extended sideways past the socket)
        core.polygon(cr, [(-1.6 * rx, top[0][1])] + top + [(1.6 * rx, top[-1][1]), (1.6 * rx, 3.0 * ry),
                                                         (-1.6 * rx, 3.0 * ry)])

    def above_bot():
        core.polygon(cr, [(-1.6 * rx, bot[0][1])] + bot + [(1.6 * rx, bot[-1][1]), (1.6 * rx, -3.0 * ry),
                                                         (-1.6 * rx, -3.0 * ry)])

    if visible:
        cr.save()
        sock.add(cr)
        cr.clip()
        # the eyeball shows only below the upper lid AND above the lower one: two clips, so the
        # corners never invert (base.eye's single polygon crosses itself there)
        cr.new_path()
        below_top()
        cr.clip()
        cr.new_path()
        above_bot()
        cr.clip()
        # sclera with the upper-lid shadow band
        sc = core.col(sclera)
        g = cairo.LinearGradient(0, -ry, 0, ry)
        sh = core.mix(sc, sk.shadow, 0.55)
        ytop_mid = y_top(0.0)
        f = clamp((ytop_mid + ry) / (2 * ry))
        g.add_color_stop_rgb(0.0, *sh[:3])
        g.add_color_stop_rgb(clamp(f + 0.02), *sh[:3])
        g.add_color_stop_rgb(clamp(f + 0.28), *core.mix(sc, sh, 0.15)[:3])
        g.add_color_stop_rgb(1.0, *sc[:3])
        cr.set_source(g)
        cr.paint()
        # iris
        ir = ry * iris_size
        ix = look[0] * rx * 0.42 * outer / max(0.4, foreshort)
        ix = clamp(ix, -rx + ir * 0.6, rx - ir * 0.6)
        iy = look[1] * ry * 0.38 + ry * 0.06
        ic = core.col(iris)
        ih = core.col(iris_hi) if iris_hi else core.tint(ic, 0.35)
        idark = core.shade(ic, 0.55)
        gi = cairo.RadialGradient(ix, iy + ir * 0.35, ir * 0.05, ix, iy, ir)
        gi.add_color_stop_rgb(0.0, *ih[:3])
        gi.add_color_stop_rgb(0.55, *ic[:3])
        gi.add_color_stop_rgb(0.86, *core.shade(ic, 0.25)[:3])
        gi.add_color_stop_rgb(1.0, *idark[:3])
        cr.set_source(gi)
        core.circle(cr, ix, iy, ir)
        cr.fill()
        # pupil
        pr = ir * pupil_size * pupil_scale
        core.src(cr, pupil)
        core.ellipse(cr, ix, iy, pr * pupil_aspect, pr)
        cr.fill()
        # lid shadow over the iris top
        g2 = cairo.LinearGradient(0, ytop_mid, 0, ytop_mid + ry * 0.55)
        dk = sk.deep
        g2.add_color_stop_rgba(0.0, dk[0], dk[1], dk[2], 0.55)
        g2.add_color_stop_rgba(1.0, dk[0], dk[1], dk[2], 0.0)
        cr.set_source(g2)
        cr.paint()
        # catchlights
        if highlight > 0:
            kx_ = -0.35 * outer
            hx, hy = ix + ir * (0.32 + kx_ * 0.2), iy - ir * 0.42
            cr.set_source_rgba(1, 1, 1, 0.92 * highlight)
            core.ellipse(cr, hx, hy, ir * 0.30, ir * 0.24, -0.4)
            core.circle(cr, ix - ir * 0.35, iy + ir * 0.38, ir * 0.1)
            cr.fill()
        cr.restore()
        # heavy upper lash line, then the thin lower lid line -- kept under the lash line (past
        # half-closed its end climbs to the socket corner, above the lash line's end: an "X")
        cr.new_path()
        wt = lw * 1.7 * lash
        core.tapered(cr, top, wt, wt, profile=lambda u: wt * (0.35 + 0.65 * min(1.0, u / 0.5) if u < 0.5 else 1.0 - (0.4 - 0.4 * lash_flick) * (u - 0.5) / 0.5))
        if lash_flick > 0:
            ex, ey = top[-1]
            core.tapered(cr, [(ex - rx * 0.1, ey), (ex + rx * 0.22 * lash_flick, ey - ry * 0.25 * lash_flick)], lw * 1.4, lw * 0.15)
        core.src(cr, line_c)
        cr.fill()
        cr.save()
        cr.new_path()
        below_top()
        cr.clip()
        cr.new_path()
        wb = lw * 0.7
        core.tapered(cr, bot[2:], wb, wb, profile=lambda u: wb * (0.1 + 0.9 * min(1.0, u / 0.5) if u < 0.5 else 1.0 - 0.6 * (u - 0.5) / 0.5))
        core.src(cr, line_c)
        cr.fill()
        cr.restore()
    else:
        # closed eye: the lid line becomes a soft arc on the skin
        k = squint_arc
        if k >= 0.5:      # happy '^' arc: bulges upward
            pts = [(x, -ry * 0.35 * (1.0 - (x / rx) ** 2) + ry * 0.15) for x in xs]
        else:             # relaxed closed: gentle downward curve
            pts = [(x, ry * 0.28 * (1.0 - (x / rx) ** 2) - ry * 0.02) for x in xs]
        detail_line(cr, pts, lw * 1.6, line_c, 1.0, taper=(0.3, 1.0, 0.5))
    if crease > 0:
        cy2 = -ry * 1.12
        pts = [(x, cy2 - 0.18 * ry * (1 - (x / rx) ** 2) + tilt * 0.3 * ry * (x / rx)) for x in xs[1:-1]]
        detail_line(cr, pts, lw * 0.8, line_c, 0.55 * crease, taper=(0.1, 1.0, 0.2))
    if bags > 0:
        pts = [(x, ry * 1.18 + 0.12 * ry * (1 - (x / rx) ** 2)) for x in xs[2:-1]]
        detail_line(cr, pts, lw * 0.7, line_c, 0.45 * bags, taper=(0.1, 1.0, 0.1))
    cr.restore()


def eye_far(cr, head, cx, cy, rx, ry, light, lw=2.2, *, angle=0.0, foreshort=1.0, outer=1.0,
            skin="#3E6E73", line=None, lid_shade=0.12, **kw):
    """The far eye (see the module doc): its bulge past the head's silhouette (`head`: the
    head's fill paths, base.Path, in the current user space) as an outlined lid of scales,
    then eye() on top. Same arguments as eye()."""
    sk = palette(light, Mat.of(skin, sss=0.2))
    line_c = line if line is not None else sk.line

    def socket(grow=0.0):
        cr.save()
        cr.translate(cx, cy)
        if angle:
            cr.rotate(angle)
        cr.scale(foreshort * outer, 1.0)
        core.ellipse(cr, 0.0, 0.0, rx + grow, ry + grow)
        cr.restore()

    cr.save()
    cr.new_path()
    socket(lw)
    cr.clip()                                   # (keeps the group small: just this eye)
    cr.push_group()
    core.src(cr, line_c)                        # the contour: the dilated socket in ink ...
    cr.paint()
    # ... the lid skin in it: the head's lit scales, a shade darker toward the lash line
    g = cairo.LinearGradient(cx, cy - ry, cx, cy + ry)
    g.add_color_stop_rgb(0.0, *sk.lit[:3])
    g.add_color_stop_rgb(1.0, *core.shade(sk.lit, 0.5 * lid_shade)[:3])
    socket(0.0)
    cr.set_source(g)
    cr.fill()
    # inside the head's silhouette the face is already drawn: only the bulge outside it stays
    cr.set_operator(cairo.OPERATOR_CLEAR)
    for pth in head:
        pth.add(cr)
    cr.fill()
    cr.set_operator(cairo.OPERATOR_OVER)
    cr.pop_group_to_source()
    cr.paint()
    cr.restore()
    eye(cr, cx, cy, rx, ry, light, lw, angle=angle, foreshort=foreshort, outer=outer, skin=skin, line=line,
        lid_shade=lid_shade, **kw)
