"""Character rig. Body space: neck root (sternal notch) at (0,0), y down, ~116 units per head."""
import math
import cairo
from common import (clamp, lerp, mix, mul, tint, hexc, rgba, smooth_closed, smooth_open,
                    capsule, ellipse, soft_dot, shade, soft_stroke, sn)

# ---------------------------------------------------------------- characters
BASE = dict(
    skin=hexc("8f9c8a"), lip=hexc("6e6470"), hair=hexc("2a2220"), hair_hi=hexc("5a4a42"),
    brow=hexc("2a2220"), shirt=hexc("4f7478"), shirt2=hexc("3d5c60"), pants=hexc("3b3a42"),
    shoes=hexc("2b2420"), sclera=hexc("ddd8c4"), iris=hexc("e0a030"), milky=1.0, bags=0.45,
    hairstyle="messy", eye_w=20.0, eye_h=10.5, brow_t=3.0, mouth_w=14.0, jaw=1.0, chin=1.0,
    nose=1.0, collar="crew", torn=True, headset=False, helmet=False, stubble=0.0, blush=0.0,
    long_hair=False, build=1.0,
)


def make(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


ZOMBIE = make()  # the one who becomes conscious (teal shirt)
HUMAN_A = make(skin=hexc("6b4632"), lip=hexc("5a3428"), hair=hexc("151112"), hair_hi=hexc("3a2c2a"),
               brow=hexc("1a1414"), shirt=hexc("5d6b45"), shirt2=hexc("4a5636"), pants=hexc("4a5636"),
               sclera=hexc("f2eee6"), iris=hexc("3a2214"), milky=0.0, bags=0.08, hairstyle="bun",
               eye_w=19.5, eye_h=10.8, brow_t=3.1, mouth_w=13.5, jaw=0.92, chin=0.95, nose=0.95,
               collar="flight", torn=False, headset=True, blush=0.10, build=0.92)
HUMAN_B = make(skin=hexc("e2b49a"), lip=hexc("b0786a"), hair=hexc("8a4524"), hair_hi=hexc("c07040"),
               brow=hexc("7a3c20"), shirt=hexc("3e4a5c"), shirt2=hexc("2f3a4a"), pants=hexc("2f3a4a"),
               sclera=hexc("f4f0ea"), iris=hexc("4f7a8c"), milky=0.0, bags=0.12, hairstyle="short",
               eye_w=18.5, eye_h=9.8, brow_t=3.8, mouth_w=14.5, jaw=1.08, chin=1.05, nose=1.1,
               collar="flight", torn=False, headset=True, stubble=0.35, blush=0.06, build=1.06)
DEFENDER = make(skin=hexc("c89a7a"), lip=hexc("9a6a5a"), hair=hexc("3a2a20"), sclera=hexc("f0ece4"),
                iris=hexc("5a4030"), milky=0.0, bags=0.25, hairstyle="short", helmet=True,
                shirt=hexc("4a5240"), shirt2=hexc("3a4032"), collar="flight", torn=False, stubble=0.2)

SHIRTS = ["7a3b3b", "8a7a3a", "5a5a60", "6a5040", "45506e", "8a8478", "5b3f5e", "4b6040", "735a48"]
HAIRS = ["2a2220", "4a3426", "1e1a1a", "6a5a4a", "3a2a24", "5a4636"]
SKINS = ["8f9c8a", "8a9484", "96a08e", "86927f", "9aa391"]


def horde_style(i):
    from common import hsh
    lng = hsh(i, 5) < 0.4
    return make(shirt=hexc(SHIRTS[i % len(SHIRTS)]), shirt2=mul(hexc(SHIRTS[i % len(SHIRTS)]), 0.8),
                hair=hexc(HAIRS[(i * 7) % len(HAIRS)]), skin=hexc(SKINS[(i * 3) % len(SKINS)]),
                long_hair=lng, hairstyle="long" if lng else "messy",
                pants=hexc(["3b3a42", "4a4036", "2e3440", "4a4a4a"][i % 4]), build=0.9 + hsh(i, 2) * 0.2,
                eye_w=19 + hsh(i, 3) * 2, jaw=0.9 + hsh(i, 4) * 0.2)


# ---------------------------------------------------------------- expression defaults
def expr(**kw):
    e = dict(bi=0.0, bo=0.0, biL=None, biR=None, boL=None, boR=None, lid=0.0, lidL=None, lidR=None,
             low=0.0, gx=0.0, gy=0.0, op=0.0, sm=0.0, wd=0.0, tr=0.0, press=0.0, milky=None,
             glow=0.0, pupil=0.42, tears=(), t=0.0, sneer=0.0)
    e.update(kw)
    return e


# ---------------------------------------------------------------- head
def _proj(x, d, th):
    return x * math.cos(th) + d * math.sin(th)


def draw_head(ctx, ch, E, yaw, pitch, light, lw, lod=2, back=False):
    """At head centre (already rotated by roll). Head spans y -60..56."""
    th = yaw * 1.0
    s = math.sin(th)
    ph = pitch * 0.7
    pdy = math.sin(ph) * 38          # front-feature vertical shift
    skin = ch["skin"]
    op = E["op"]
    chin_drop = op * 6.0
    jw, cn = ch["jaw"], ch["chin"]

    # outline points (x, y, forward weight)
    base = [(0, -60, 0), (28, -56, 0.1), (41, -38, 0.2), (44, -12, 0.35), (43, 10, 0.5), (39 * jw, 27, 0.7),
            (31 * jw, 41, 0.85), (18 * cn, 51 + 2 * cn, 1.0), (0, 56 * cn, 1.0)]
    pts = []
    for sgn in (1, -1):
        seq = base if sgn == 1 else list(reversed(base))
        for (x, y, fw) in seq:
            if sgn == -1 and x == 0:
                continue
            xx = sgn * x
            near = 1.0 if (sgn * s) > 0 else 0.0
            xp = xx * (1 - 0.06 * abs(s)) + s * fw * (16 + 10 * near)
            yp = y + (chin_drop * clamp((y - 20) / 36) if y > 20 else 0) + pdy * fw * 0.5
            pts.append((xp, yp))
    # rotate list so it starts at crown
    def outline():
        smooth_closed(ctx, pts)

    hair = ch["hair"]
    # --- back hair (long hair / bun) behind everything
    if ch["hairstyle"] == "long" and not back:
        ctx.new_path()
        smooth_closed(ctx, [(-46 + s * 6, -30), (-50, 20), (-52, 70), (-30, 92), (30, 92), (52, 70), (50, 20), (46 + s * 6, -30), (0, -66)])
        shade(ctx, lambda: smooth_closed(ctx, [(-46 + s * 6, -30), (-50, 20), (-52, 70), (-30, 92), (30, 92), (52, 70), (50, 20), (46 + s * 6, -30), (0, -66)]),
              mul(hair, 0.85), light, lw)
    if ch["hairstyle"] == "bun":
        bx = -s * 30
        if abs(s) > 0.15 or back:
            shade(ctx, lambda: ellipse(ctx, bx * 1.4, -46, 20, 18), hair, light, lw)

    # --- ears
    ear_x = 44 * math.cos(th) - 2 * s
    ears = []
    for sgn in (1, -1):
        ex = sgn * ear_x
        zf = -sgn * s  # >0 means ear toward camera
        ears.append((sgn, ex, zf))

    def ear_path(sgn, ex):
        w = 8 * (1 - 0.5 * abs(s))
        smooth_closed(ctx, [(ex - sgn * 2, -10 + pdy * 0.2), (ex + sgn * w, -9), (ex + sgn * (w + 1.5), 4),
                            (ex + sgn * w * 0.6, 17), (ex - sgn * 1, 15)])

    def draw_ear(sgn, ex):
        shade(ctx, lambda: ear_path(sgn, ex), skin, light, lw, shadow=0.3)
        if lod > 1:
            soft_stroke(ctx, [(ex + sgn * 2, -5), (ex + sgn * 5, 0), (ex + sgn * 4, 9)], mul(skin, 0.6), 0.35, lw * 1.2)

    for sgn, ex, zf in ears:
        if zf <= 0.12 and not (ch["headset"] and not back):
            draw_ear(sgn, ex)

    # --- head fill
    if back:
        shade(ctx, outline, hair, light, lw, shadow=0.35)
        # nape skin
        ctx.save()
        ctx.new_path(); outline(); ctx.clip()
        rgba(ctx, tint(skin, light))
        ctx.new_path(); ellipse(ctx, 0, 60, 30, 16); ctx.fill()
        ctx.restore()
        for sgn, ex, zf in ears:
            if not ch["headset"]:
                draw_ear(sgn, ex)
        if ch["headset"]:
            _headset(ctx, ch, s, ear_x, pdy, light, lw, back=True)
        if ch["helmet"]:
            _helmet(ctx, s, light, lw)
        return

    shade(ctx, outline, skin, light, lw, shadow=0.42)
    if lod <= 0:
        _hair_front(ctx, ch, s, th, pdy, light, lw, lod)
        return

    # face form shading: cheek hollows, jaw shadow, temple
    ctx.save()
    ctx.new_path(); outline(); ctx.clip()
    lx = light["dir"][0]
    soft_dot(ctx, -lx * 30 + s * 10, 18, 26, light["shadow"], 0.16)
    soft_dot(ctx, lx * 22 + s * 14, -26, 30, light["rim"], 0.10)
    if ch["blush"] > 0:
        for sgn in (1, -1):
            soft_dot(ctx, _proj(sgn * 24, 30, th), 16 + pdy * 0.8, 12, hexc("d06a5a"), ch["blush"])
    if ch["stubble"] > 0:
        rgba(ctx, mul(ch["hair"], 0.7), ch["stubble"] * 0.45)
        ctx.new_path()
        smooth_closed(ctx, [(_proj(-38, 10, th), 18 + pdy * 0.6), (_proj(-26, 30, th), 44), (_proj(0, 38, th), 58 + chin_drop),
                            (_proj(26, 30, th), 44), (_proj(38, 10, th), 18 + pdy * 0.6), (_proj(14, 40, th), 30 + pdy),
                            (_proj(0, 42, th), 22 + pdy), (_proj(-14, 40, th), 30 + pdy)])
        ctx.fill()
    ctx.restore()

    # --- near ears (3/4 view)
    for sgn, ex, zf in ears:
        if zf > 0.12 and not ch["headset"]:
            draw_ear(sgn, ex)

    # --- eyes, brows
    ew, eh = ch["eye_w"], ch["eye_h"]
    ey = -2 + pdy
    milky = ch["milky"] if E["milky"] is None else E["milky"]
    for sgn in (1, -1):
        ex = _proj(sgn * 17, 36, th)
        fs = clamp(math.cos(th + math.asin(sgn * 0.42)), 0.18, 1.0)
        lid = E["lidR"] if sgn == 1 and E["lidR"] is not None else E["lidL"] if sgn == -1 and E["lidL"] is not None else E["lid"]
        bi = E["biR"] if sgn == 1 and E["biR"] is not None else E["biL"] if sgn == -1 and E["biL"] is not None else E["bi"]
        bo = E["boR"] if sgn == 1 and E["boR"] is not None else E["boL"] if sgn == -1 and E["boL"] is not None else E["bo"]
        # brows raised pull upper lid open a touch; worry lowers outer lid
        _eye(ctx, ch, ex, ey, ew * fs, eh, sgn, clamp(lid - 0.12 * max(0, bi + bo) / 2), E["low"],
             E["gx"], E["gy"], milky, E["glow"], E["pupil"], light, lw, lod, pitch)
        _brow(ctx, ch, ex, ey, ew * fs, eh, sgn, bi, bo, light, lw, s)
    # forehead / frown lines (anatomical, faint)
    if lod > 1:
        bi_avg = E["bi"] if E["biL"] is None else (E["biL"] + (E["biR"] if E["biR"] is not None else E["bi"])) / 2
        if bi_avg > 0.35:
            a = (bi_avg - 0.35) * 0.35
            for k in range(2):
                yy = -30 - k * 6 + pdy * 0.3
                soft_stroke(ctx, [(_proj(-14, 40, th), yy + 1), (_proj(0, 42, th), yy - 1), (_proj(14, 40, th), yy + 1)],
                            mul(skin, 0.55), a, lw * 0.9)
        if bi_avg < -0.3:
            a = (-bi_avg - 0.3) * 0.5
            for sgn in (1, -1):
                xx = _proj(sgn * 4, 42, th)
                soft_stroke(ctx, [(xx, -18 + pdy), (xx + sgn * 1, -10 + pdy)], mul(skin, 0.5), a, lw)

    # --- nose
    _nose(ctx, ch, th, s, pdy, light, lw, lod)
    # --- mouth
    mx = _proj(0, 40, th)
    my = 30 + pdy * 0.95
    _mouth(ctx, ch, mx, my, E, light, lw, math.cos(th), lod)
    # --- tears
    for (sgn, prog, alpha) in E["tears"]:
        ex = _proj(sgn * 17, 36, th)
        _tear(ctx, ex + sgn * 2, ey + eh * 0.55, prog, alpha, lw, sgn, s)

    _hair_front(ctx, ch, s, th, pdy, light, lw, lod)
    if ch["headset"]:
        _headset(ctx, ch, s, ear_x, pdy, light, lw)
    if ch["helmet"]:
        _helmet(ctx, s, light, lw)


def _eye(ctx, ch, cx, cy, w, h, sgn, lid, low, gx, gy, milky, glow, pupil, light, lw, lod, pitch):
    inner = cx - sgn * w / 2
    outer = cx + sgn * w / 2
    iy, oy = cy + 0.5, cy - 0.8
    hu = h * (1.0 - 1.18 * lid) - pitch * 2.0
    hl = h * 0.48 * (1 - 0.6 * low)
    pk = inner + (outer - inner) * 0.42
    pl = inner + (outer - inner) * 0.55
    up_c = (pk, cy - hu)

    def upper(move=True):
        if move:
            ctx.move_to(inner, iy)
        ctx.curve_to(inner + (pk - inner) * 0.35, up_c[1] + hu * 0.05, pk - (outer - pk) * 0.2, up_c[1], pk, up_c[1])
        ctx.curve_to(pk + (outer - pk) * 0.45, up_c[1], outer - (outer - pk) * 0.15, oy - hu * 0.25, outer, oy)

    def lower():
        ctx.curve_to(outer - (outer - pl) * 0.3, cy + hl * 0.9, pl + (outer - pl) * 0.3, cy + hl, pl, cy + hl)
        ctx.curve_to(pl - (pl - inner) * 0.5, cy + hl, inner + (pl - inner) * 0.15, iy + hl * 0.5, inner, iy)

    skin = ch["skin"]
    # socket / bags
    if lod > 1:
        soft_dot(ctx, cx, cy - 1, w * 0.95, light["shadow"], 0.10 + ch["bags"] * 0.1)
        if ch["bags"] > 0:
            soft_dot(ctx, cx + sgn * 2, cy + h * 0.95, w * 0.55, hexc("4a3a5a"), ch["bags"] * 0.45)
    if hu > h * 0.1:
        ctx.save()
        ctx.new_path(); upper(); lower(); ctx.close_path()
        ctx.clip_preserve()
        rgba(ctx, tint(ch["sclera"], light))
        ctx.fill()
        ir = h * 0.56
        ix = cx + gx * w * 0.27
        iyc = cy + gy * h * 0.22 - h * 0.04
        icol = mix(ch["iris"], hexc("cfd2cc"), milky)
        g = cairo.RadialGradient(ix, iyc, ir * 0.1, ix, iyc, ir)
        g.add_color_stop_rgb(0, *mix(icol, (1, 1, 1), 0.25 + 0.3 * glow))
        g.add_color_stop_rgb(0.7, *icol)
        g.add_color_stop_rgb(1, *mul(icol, 0.55 + 0.3 * milky))
        ctx.set_source(g)
        ctx.new_path(); ctx.arc(ix, iyc, ir, 0, 2 * math.pi); ctx.fill()
        pa = 1 - milky * 0.92
        rgba(ctx, hexc("0c0a0c"), pa)
        ctx.new_path(); ctx.arc(ix, iyc, ir * pupil, 0, 2 * math.pi); ctx.fill()
        # lid shadow on eyeball
        g = cairo.LinearGradient(0, cy - hu, 0, cy - hu + h * 0.7)
        g.add_color_stop_rgba(0, *light["shadow"], 0.45)
        g.add_color_stop_rgba(1, *light["shadow"], 0)
        ctx.set_source(g)
        ctx.paint()
        # catchlights
        rgba(ctx, (1, 1, 1), 0.95 - milky * 0.5)
        ctx.new_path(); ctx.arc(ix - ir * 0.32, iyc - ir * 0.38, ir * 0.24, 0, 2 * math.pi); ctx.fill()
        rgba(ctx, (1, 1, 1), 0.5 - milky * 0.3)
        ctx.new_path(); ctx.arc(ix + ir * 0.3, iyc + ir * 0.28, ir * 0.1, 0, 2 * math.pi); ctx.fill()
        ctx.restore()
        if glow > 0:
            soft_dot(ctx, ix, iyc, ir * 2.6, hexc("ffcf70"), 0.35 * glow)
        # lash line + lower lid
        ctx.new_path(); upper()
        rgba(ctx, mul(ch["hair"], 0.6) if ch["hair"][0] < 0.5 else hexc("2a1a14"), 0.95)
        ctx.set_line_width(lw * 1.9)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        if lod > 1:
            ctx.new_path(); ctx.move_to(outer, oy); lower()
            rgba(ctx, mul(skin, 0.5), 0.35)
            ctx.set_line_width(lw * 0.9)
            ctx.stroke()
    else:
        # closed: lid line curves down
        ctx.new_path()
        ctx.move_to(inner, iy)
        ctx.curve_to(inner + (outer - inner) * 0.3, cy + h * 0.32, inner + (outer - inner) * 0.7, cy + h * 0.32, outer, oy)
        rgba(ctx, hexc("241a1c"), 0.9)
        ctx.set_line_width(lw * 1.7)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    # crease
    if lod > 1:
        cr = cy - h * (1.05 + 0.25 * (1 - lid))
        soft_stroke(ctx, [(inner + sgn * 1.5, iy - h * 0.6), (pk, cr), (outer - sgn * 1, oy - h * 0.5)], mul(skin, 0.55), 0.32, lw * 0.9)


def _brow(ctx, ch, cx, cy, w, h, sgn, bi, bo, light, lw, s):
    t = ch["brow_t"]
    fur = max(0.0, -bi)
    inner = (cx - sgn * (w * 0.45 - fur * 2.2), cy - h * 1.55 - max(0, bi) * 5.5 + fur * 3.0)
    mid = (cx + sgn * w * 0.12, cy - h * 1.95 - (max(0, bi) * 2.5 + bo * 3.5) + fur * 1.2)
    outer = (cx + sgn * w * 0.66, cy - h * 1.55 - bo * 4.0 + max(0, bi) * 0.8)
    pts = []
    for k in range(9):
        u = k / 8
        x = (1 - u) ** 2 * inner[0] + 2 * u * (1 - u) * mid[0] + u * u * outer[0]
        y = (1 - u) ** 2 * inner[1] + 2 * u * (1 - u) * mid[1] + u * u * outer[1]
        pts.append((x, y))
    th = [t * (1.0 - 0.65 * (k / 8) ** 1.5) for k in range(9)]
    top, bot = [], []
    for k, (x, y) in enumerate(pts):
        a = pts[min(k + 1, 8)]
        b = pts[max(k - 1, 0)]
        dx, dy = a[0] - b[0], a[1] - b[1]
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        if ny > 0:
            nx, ny = -nx, -ny
        top.append((x + nx * th[k] * 0.55, y + ny * th[k] * 0.55))
        bot.append((x - nx * th[k] * 0.45, y - ny * th[k] * 0.45))
    ctx.new_path()
    smooth_open(ctx, top)
    smooth_open(ctx, list(reversed(bot)), move=False)
    ctx.close_path()
    rgba(ctx, tint(ch["brow"], light), 0.92)
    ctx.fill_preserve()
    rgba(ctx, tint(ch["brow"], light), 0.3)
    ctx.set_line_width(lw * 0.8)
    ctx.stroke()


def _nose(ctx, ch, th, s, pdy, light, lw, lod):
    k = ch["nose"]
    bx = _proj(0, 44, th)
    tx = _proj(0, 52 * k, th)
    ty = 15 * k + pdy * 0.9
    skin = ch["skin"]
    lx = light["dir"][0]
    sd = -1 if lx > 0 else 1
    # bridge shadow on the side away from light
    soft_stroke(ctx, [(bx + sd * 5, -6 + pdy * 0.6), (tx + sd * 6, ty - 6)], light["shadow"], 0.10, lw * 3)
    # under-nose shadow
    soft_dot(ctx, tx, ty + 5, 9 * k, light["shadow"], 0.20)
    if lod > 1:
        # nostrils (soft, no outlines)
        for sg in (1, -1):
            nx = tx + sg * 5.2 * k * math.cos(th) - s * 1.5
            soft_dot(ctx, nx, ty + 2.2, 3.2 * k, hexc("2a1a1c"), 0.55 * (1 - 0.6 * max(0, sg * s)))
        # alar wings
        for sg in (1, -1):
            wx = tx + sg * 8 * k * math.cos(th)
            soft_stroke(ctx, [(wx, ty - 3), (wx + sg * 1.5, ty + 0.5), (wx - sg * 2, ty + 3)], mul(skin, 0.55), 0.35, lw * 0.9)
        soft_dot(ctx, tx - lx * 2, ty - 2.5, 4.5, light["rim"], 0.18)
    # profile edge when turned
    if abs(s) > 0.12:
        sg = 1 if s > 0 else -1
        soft_stroke(ctx, [(bx + sg * 2, -4 + pdy * 0.6), (tx + sg * 3.5, ty - 1), (tx + sg * 1, ty + 3.5)],
                    mul(skin, 0.45), min(0.6, abs(s) * 1.4), lw * 1.1)


def _mouth(ctx, ch, mx, my, E, light, lw, cth, lod):
    op = clamp(E["op"])
    sm = E["sm"]
    wd = E["wd"]
    tr = E["tr"] * math.sin(E["t"] * 9.0) * 0.6 + E["tr"] * math.sin(E["t"] * 5.3) * 0.4
    hw = ch["mouth_w"] * (1 + 0.22 * wd + 0.07 * sm - 0.28 * op) * (0.55 + 0.45 * cth)
    cyl = my + 0.9 - sm * 3.4 + tr * 0.9 + max(0, -sm) * 0.6 + op * 2.2
    cyr = my + 0.9 - sm * 3.4 - tr * 0.7 + max(0, -sm) * 0.6 + op * 2.2
    cl, cr = (mx - hw, cyl), (mx + hw, cyr)
    top_y = my - op * 1.2 - E["sneer"] * 2
    bot_y = my + op * 15 + 0.8 + E["press"] * -0.5
    lipc = ch["lip"]
    # lips
    up_out = [(cl[0], cl[1]), (mx - hw * 0.38, my - 4.6 - op * 2), (mx, my - 3.4 - op * 2), (mx + hw * 0.38, my - 4.6 - op * 2), (cr[0], cr[1])]
    ctx.new_path(); smooth_open(ctx, up_out)
    ctx.curve_to(mx + hw * 0.5, top_y, mx - hw * 0.5, top_y, cl[0], cl[1])
    rgba(ctx, tint(lipc, light), 0.55 - E["press"] * 0.25)
    ctx.fill()
    lo_bot = bot_y + 6.5 - E["press"] * 2
    ctx.new_path(); ctx.move_to(*cl)
    ctx.curve_to(mx - hw * 0.55, bot_y, mx + hw * 0.55, bot_y, cr[0], cr[1])
    ctx.curve_to(mx + hw * 0.6, lo_bot, mx - hw * 0.6, lo_bot, cl[0], cl[1])
    rgba(ctx, tint(mix(lipc, ch["skin"], 0.25), light), 0.55 - E["press"] * 0.25)
    ctx.fill()
    if lod > 1:
        soft_dot(ctx, mx, bot_y + 3, hw * 0.35, light["rim"], 0.12)
        soft_dot(ctx, mx, lo_bot + 3.5, hw * 0.55, light["shadow"], 0.16)
    if op > 0.04:
        ctx.save()
        ctx.new_path(); ctx.move_to(*cl)
        ctx.curve_to(mx - hw * 0.5, top_y, mx + hw * 0.5, top_y, cr[0], cr[1])
        ctx.curve_to(mx + hw * 0.55, bot_y, mx - hw * 0.55, bot_y, cl[0], cl[1])
        ctx.close_path()
        rgba(ctx, hexc("3a1418"))
        ctx.fill_preserve()
        ctx.clip()
        if op > 0.12:
            rgba(ctx, hexc("e8e2d6"), 0.9)
            ctx.new_path(); ctx.rectangle(mx - hw * 0.62, top_y - 3, hw * 1.24, 2.4 + min(3.5, op * 6)); ctx.fill()
            rgba(ctx, hexc("a04858"), 0.85)
            ctx.new_path(); ellipse(ctx, mx, bot_y - 1, hw * 0.55, max(1, op * 5)); ctx.fill()
        ctx.restore()
        ctx.new_path(); ctx.move_to(*cl)
        ctx.curve_to(mx - hw * 0.5, top_y, mx + hw * 0.5, top_y, cr[0], cr[1])
        ctx.curve_to(mx + hw * 0.55, bot_y, mx - hw * 0.55, bot_y, cl[0], cl[1])
        rgba(ctx, hexc("1c1012"), 0.85)
        ctx.set_line_width(lw * 1.1)
        ctx.stroke()
    else:
        ctx.new_path(); ctx.move_to(*cl)
        ctx.curve_to(mx - hw * 0.45, my + 0.2 + sm * 0.6, mx + hw * 0.45, my + 0.2 + sm * 0.6, cr[0], cr[1])
        rgba(ctx, hexc("2a1618"), 0.85)
        ctx.set_line_width(lw * 1.25)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    if lod > 1:
        for c in (cl, cr):
            soft_dot(ctx, c[0], c[1], 3.2, hexc("2a1618"), 0.35)


def _tear(ctx, x0, y0, prog, alpha, lw, sgn, s):
    if alpha <= 0 or prog <= 0:
        return
    path = [(x0, y0), (x0 + sgn * 3, y0 + 14), (x0 + sgn * 4, y0 + 28), (x0 + sgn * 2, y0 + 44)]
    k = clamp(prog)
    n = 1 + int(k * 3)
    seg = path[: n + 1]
    # interpolate head position
    fpos = k * 3
    i = min(2, int(fpos))
    u = fpos - i
    hx = lerp(path[i][0], path[i + 1][0], u)
    hy = lerp(path[i][1], path[i + 1][1], u)
    trail = path[: i + 1] + [(hx, hy)]
    blue = hexc("a8d4f0")
    soft_stroke(ctx, trail, blue, 0.35 * alpha, lw * 1.2)
    ctx.new_path()
    ctx.move_to(hx, hy - 4.5)
    ctx.curve_to(hx + 2.6, hy - 1, hx + 2.8, hy + 2.6, hx, hy + 2.8)
    ctx.curve_to(hx - 2.8, hy + 2.6, hx - 2.6, hy - 1, hx, hy - 4.5)
    rgba(ctx, blue, 0.75 * alpha)
    ctx.fill()
    rgba(ctx, (1, 1, 1), 0.85 * alpha)
    ctx.new_path(); ctx.arc(hx - 0.9, hy - 0.2, 0.9, 0, 2 * math.pi); ctx.fill()


def _cap_outer(s, top=-62, vol=1.05, side_y=-2):
    base = [(45, side_y, 0.42), (45, -16, 0.35), (42, -38, 0.2), (29, -57, 0.1), (0, top, 0.0)]
    pts = []
    for sgn in (1, -1):
        seq = base if sgn == 1 else list(reversed(base))
        for (x, y, fw) in seq:
            if sgn == -1 and x == 0:
                continue
            near = 1.0 if sgn * s > 0 else 0.0
            xp = sgn * x * (1 - 0.06 * abs(s)) + s * fw * (16 + 10 * near)
            pts.append((xp * vol, -10 + (y + 10) * vol))
    return pts


def _hairline(th, pts, pdy):
    out = []
    for (x, y) in pts:
        d = 4 + 10 * (1 - min(1, abs(x) / 45))
        out.append((_proj(x, d, th), y + pdy * 0.25))
    return out


def _hair_front(ctx, ch, s, th, pdy, light, lw, lod):
    hair = ch["hair"]
    hs = ch["hairstyle"]
    fx = lambda x, d: _proj(x, d, th)
    hi = tint(ch["hair_hi"], light)
    if hs in ("messy", "long"):
        cap = _cap_outer(s, -63) + _hairline(th, [(-42, -16), (-31, -28), (-12, -34), (10, -35), (30, -29), (42, -16)], pdy)
        shade(ctx, lambda: smooth_closed(ctx, cap), hair, light, lw, shadow=0.4)
        if lod > 0:
            locks = [(-30, -28, -35, -15), (-17, -33, -21, -19), (-5, -35, -3, -22), (7, -35, 11, -20), (19, -32, 23, -18), (31, -27, 35, -15)]
            for i, (x0, y0, x1, y1) in enumerate(locks):
                a0, a1 = fx(x0, 14), fx(x1, 18)
                b0 = y0 + pdy * 0.3
                b1 = y1 + pdy * 0.35
                ctx.new_path()
                ctx.move_to(a0 - 7, b0 - 6)
                ctx.curve_to(a0 - 4, b0 + 4, a1 - 2, b1 - 6, a1, b1)
                ctx.curve_to(a1 + 2, b1 - 7, a0 + 7, b0, a0 + 8, b0 - 7)
                ctx.close_path()
                rgba(ctx, tint(hair, light))
                ctx.fill_preserve()
                rgba(ctx, light.get("line", (0.1, 0.08, 0.1)), 0.5)
                ctx.set_line_width(lw * 0.8)
                ctx.stroke()
            if lod > 1:
                for i in range(7):
                    x = -30 + i * 10
                    soft_stroke(ctx, [(fx(x * 0.9, 4), -60 + abs(x) * 0.3), (fx(x + 3, 10), -48), (fx(x + 5, 14), -38 + pdy * 0.25)],
                                hi, 0.45, lw * 0.8)
        if hs == "long" and lod > 0:
            for sgn in (1, -1):
                ox = _cap_outer(s, -63)[0 if sgn == 1 else -1][0]
                side = [(ox - sgn * 4, -20), (ox + sgn * 3, 4), (ox + sgn * 5, 40), (ox, 70), (ox - sgn * 5, 40), (ox - sgn * 4, 2)]
                shade(ctx, lambda: smooth_closed(ctx, side), hair, light, lw, shadow=0.35)
    elif hs == "short":
        cap = _cap_outer(s, -74, 1.06, side_y=4) + _hairline(th, [(-42, -10), (-36, -30), (-18, -42), (4, -45), (26, -39), (42, -14)], pdy)
        shade(ctx, lambda: smooth_closed(ctx, cap), hair, light, lw, shadow=0.35)
        if lod > 1:
            for i in range(6):
                x = -28 + i * 11
                soft_stroke(ctx, [(fx(x - 8, 4), -66), (fx(x + 2, 10), -56), (fx(x + 10, 14), -46 + pdy * 0.25)], hi, 0.4, lw * 0.8)
    elif hs == "bun":
        cap = _cap_outer(s, -64, 1.03) + _hairline(th, [(-42, -12), (-34, -32), (-14, -44), (12, -44), (34, -32), (42, -12)], pdy)
        shade(ctx, lambda: smooth_closed(ctx, cap), hair, light, lw, shadow=0.3)
        if lod > 1:
            for i in range(5):
                x = -24 + i * 12
                soft_stroke(ctx, [(fx(x, 12), -44 + pdy * 0.25), (fx(x * 0.8, 6), -56), (fx(x * 0.4, 2), -63)], hi, 0.35, lw * 0.8)


def _headset(ctx, ch, s, ear_x, pdy, light, lw, back=False):
    dark = hexc("2c2f33")
    # band hugging the skull
    ctx.new_path()
    ctx.move_to(-ear_x - 2, -8)
    ctx.curve_to(-ear_x - 6, -60, ear_x + 6, -60, ear_x + 2, -8)
    rgba(ctx, tint(dark, light))
    ctx.set_line_width(7)
    ctx.stroke_preserve()
    rgba(ctx, light.get("line"), 0.8)
    ctx.set_line_width(1.2)
    ctx.stroke()
    for sgn in (1, -1):
        ex = sgn * ear_x
        if (-sgn * s) < -0.35 and not back:
            continue
        shade(ctx, lambda: (ctx.new_sub_path(), _rrect(ctx, ex - 9, -12, 18, 28, 8)), dark, light, lw, shadow=0.3)
        soft_dot(ctx, ex - light["dir"][0] * 3, -4, 6, light["rim"], 0.25)
    if not back:
        # mic boom on the character's left (screen right)
        ex = ear_x
        mx = _proj(14, 40, s)
        ctx.new_path()
        ctx.move_to(ex - 2, 8)
        ctx.curve_to(ex - 4, 30, mx + 14, 40, mx + 6, 38 + pdy * 0.6)
        rgba(ctx, tint(dark, light))
        ctx.set_line_width(3)
        ctx.stroke()
        shade(ctx, lambda: ellipse(ctx, mx + 5, 38 + pdy * 0.6, 5, 4), hexc("1c1e20"), light, lw * 0.7)


def _helmet(ctx, s, light, lw):
    col = hexc("4a5240")
    shade(ctx, lambda: (ctx.move_to(-50, -8), ctx.curve_to(-54, -82, 54, -82, 50, -8), ctx.line_to(44, -14),
                        ctx.curve_to(30, -24, -30, -24, -44, -14), ctx.close_path()), col, light, lw)
    shade(ctx, lambda: (ctx.move_to(-54, -10), ctx.curve_to(-30, -24, 30, -24, 54, -10), ctx.line_to(54, -3),
                        ctx.curve_to(30, -17, -30, -17, -54, -3), ctx.close_path()), mul(col, 0.7), light, lw)
    soft_dot(ctx, -14, -58, 24, light["rim"], 0.3)
    soft_stroke(ctx, [(-46, -4), (-38, 30), (-20, 52)], hexc("2a2a24"), 0.8, 2.2)


def _rrect(ctx, x, y, w, h, r):
    ctx.move_to(x + r, y)
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


# ---------------------------------------------------------------- hands
FING = [(-11.5, 38, 4.9), (-3.9, 42, 5.1), (3.9, 39, 4.8), (11.2, 31, 4.2)]  # (y at knuckle, length, radius)


def hand_parts(curl=0.2, spread=0.3, thumb=0.4, fcurl=None):
    """Return dict of shapes in hand-local coords (wrist origin, +x to fingers, thumb at -y)."""
    palm = [(0, -11), (8, -14.5), (34, -16.5), (39, -12), (40, 0), (39, 12.5), (34, 16), (8, 13), (0, 10)]
    fingers = []
    for i, (fy, ln, r) in enumerate(FING):
        c = curl if fcurl is None else fcurl[i]
        ang = [-0.11, -0.03, 0.05, 0.13][i] * (0.4 + spread)
        base = (36, fy)
        segs = [0.46, 0.30, 0.24]
        bends = [0.95, 1.65, 2.1]
        pts = [base]
        x, y = base
        for sl, bd in zip(segs, bends):
            cum = c * bd
            adv = ln * sl * math.cos(cum)
            x += adv * math.cos(ang)
            y += adv * math.sin(ang)
            pts.append((x, y))
        fingers.append((pts, r, c))
    ta = lerp(-1.05, -0.2, thumb)
    tb = (9, -10.5)
    t1 = (tb[0] + 17 * math.cos(ta), tb[1] + 17 * math.sin(ta))
    ta2 = ta + 0.35 + thumb * 0.3
    t2 = (t1[0] + 14 * math.cos(ta2), t1[1] + 14 * math.sin(ta2))
    return palm, fingers, (tb, t1, t2)


def draw_hand(ctx, ch, x, y, ang, light, lw, curl=0.2, spread=0.3, thumb=0.4, flip=False, palm_view=False,
              size=1.0, fcurl=None, lod=2, hfs=1.0):
    skin = ch["skin"]
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(size * hfs, -size if flip else size)
    lw2 = lw / size
    palm, fingers, thumbp = hand_parts(curl, spread, thumb, fcurl)

    def finger_path(pts, r):
        n = len(pts)
        for i in range(n - 1):
            r0 = r * (1 - 0.12 * i)
            r1 = r * (1 - 0.12 * (i + 1)) * (0.92 if i == n - 2 else 1)
            capsule(ctx, pts[i], pts[i + 1], r0, r1)

    def thumb_path():
        tb, t1, t2 = thumbp
        capsule(ctx, (tb[0] + 4, tb[1] + 3), tb, 8, 7.2)
        capsule(ctx, tb, t1, 7.2, 5.8)
        capsule(ctx, t1, t2, 5.8, 4.6)

    def palm_path():
        smooth_closed(ctx, palm)

    folded = []
    for pts, r, c in fingers:
        folded.append(c > 0.55)
    # pass 1: union outline
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    rgba(ctx, light.get("line", (0.1, 0.08, 0.1)), 0.9)
    ctx.set_line_width(lw2 * 2.0)
    for pts, r, c in fingers:
        ctx.new_path(); finger_path(pts, r); ctx.stroke()
    ctx.new_path(); thumb_path(); ctx.stroke()
    ctx.new_path(); palm_path(); ctx.stroke()
    col = mix(tint(skin, light), light["shadow"], 0.16)
    sh = light["shadow"]
    # pass 2: fills
    if not palm_view:
        for (pts, r, c), fo in zip(fingers, folded):
            rgba(ctx, col); ctx.new_path(); finger_path(pts, r); ctx.fill()
        rgba(ctx, col); ctx.new_path(); thumb_path(); ctx.fill()
        rgba(ctx, col); ctx.new_path(); palm_path(); ctx.fill()
        # knuckle shading (soft, no lines)
        if lod > 1:
            for pts, r, c in fingers:
                soft_dot(ctx, pts[0][0] - 1, pts[0][1], r * 1.4, light["rim"], 0.18)
                soft_dot(ctx, pts[0][0] + 4, pts[0][1], r * 1.2, sh, 0.10)
            soft_dot(ctx, 16, 2, 16, sh, 0.12)
    else:
        rgba(ctx, col); ctx.new_path(); palm_path(); ctx.fill()
        soft_dot(ctx, 22, 2, 15, mix(col, (1, 0.85, 0.8), 0.3), 0.35)
        for pts, r, c in fingers:
            if c > 0.3:
                ctx.save(); ctx.translate(1.5, 1.5)
                rgba(ctx, sh, 0.18); ctx.new_path(); finger_path(pts, r * 1.15); ctx.fill()
                ctx.restore()
            rgba(ctx, col); ctx.new_path(); finger_path(pts, r); ctx.fill()
        rgba(ctx, sh, 0.15); ctx.new_path(); ctx.save(); ctx.translate(1.5, 1.5); thumb_path(); ctx.restore(); ctx.fill()
        rgba(ctx, col); ctx.new_path(); thumb_path(); ctx.fill()
    # form shadow along the pinky side
    ctx.save()
    ctx.new_path(); palm_path(); ctx.clip()
    g = cairo.LinearGradient(0, -16, 0, 16)
    g.add_color_stop_rgba(0, *sh, 0.0)
    g.add_color_stop_rgba(1, *sh, 0.28)
    ctx.set_source(g); ctx.paint()
    ctx.restore()
    ctx.restore()


# ---------------------------------------------------------------- body
def ik(sh, tgt, l1, l2, bend=1):
    dx, dy = tgt[0] - sh[0], tgt[1] - sh[1]
    d = clamp(math.hypot(dx, dy), 1e-3, l1 + l2 - 1e-3)
    a = math.atan2(dy, dx)
    c = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)
    b = math.acos(c) * bend
    el = (sh[0] + l1 * math.cos(a - b), sh[1] + l1 * math.sin(a - b))
    k = l2 / math.hypot(tgt[0] - el[0], tgt[1] - el[1]) if (tgt[0], tgt[1]) != el else 1
    wr = (el[0] + (tgt[0] - el[0]) * min(1, k), el[1] + (tgt[1] - el[1]) * min(1, k))
    return el, wr


def arm_joints(arm, sh, bw):
    l1, l2 = 108 * bw * arm.get("fs1", 1.0), 98 * bw * arm.get("fs2", 1.0)
    if "wr" in arm:
        return arm["el"], arm["wr"]
    if "tgt" in arm:
        el, wr = ik(sh, arm["tgt"], l1, l2, arm.get("bend", 1))
    else:
        a1 = math.radians(arm.get("a1", 8))
        a2 = math.radians(arm.get("a2", 4))
        el = (sh[0] + l1 * math.sin(a1), sh[1] + l1 * math.cos(a1))
        wr = (el[0] + l2 * math.sin(a2), el[1] + l2 * math.cos(a2))
    return el, wr


def draw_arm(ctx, ch, sh, arm, light, lw, bw, lod, sgn):
    el, wr = arm_joints(arm, sh, bw)
    shirt = ch["shirt"]
    fa = math.atan2(wr[1] - el[1], wr[0] - el[0])
    hang = arm.get("hand_ang", fa)
    # hand first so the cuff covers the wrist
    def hand():
        if lod > 1:
            draw_hand(ctx, ch, wr[0] - math.cos(fa) * 4, wr[1] - math.sin(fa) * 4, hang, light, lw,
                      curl=arm.get("curl", 0.25), spread=arm.get("spread", 0.3), thumb=arm.get("thumb", 0.4),
                      flip=arm.get("flip", sgn < 0), palm_view=arm.get("palm", False), size=bw * arm.get("hs", 1.0),
                      fcurl=arm.get("fcurl"), lod=lod, hfs=arm.get("hfs", 1.0))
        else:
            shade(ctx, lambda: capsule(ctx, wr, (wr[0] + 30 * math.cos(hang), wr[1] + 30 * math.sin(hang)), 12, 9),
                  ch["skin"], light, lw)
    hand_first = arm.get("hand_behind", False)
    if hand_first:
        hand()
    path = lambda: (capsule(ctx, sh, el, 16 * bw, 13 * bw), capsule(ctx, el, wr, 13.5 * bw, 10.5 * bw))
    shade(ctx, path, shirt, light, lw, shadow=0.42, union=True)
    if lod > 1:
        # elbow fold
        mx, my = el
        soft_stroke(ctx, [(mx - 6 * math.cos(fa + 1.2), my - 6 * math.sin(fa + 1.2)), (mx, my), (mx + 4 * math.cos(fa), my + 4 * math.sin(fa))],
                    mul(shirt, 0.55), 0.35, lw)
    if not hand_first:
        hand()
    # cuff (sleeve opening) over the wrist
    c0 = (wr[0] - math.cos(fa) * 9, wr[1] - math.sin(fa) * 9)
    c1 = (wr[0] - math.cos(fa) * 1, wr[1] - math.sin(fa) * 1)
    shade(ctx, lambda: capsule(ctx, c0, c1, 11.5 * bw, 12 * bw), ch["shirt2"], light, lw, shadow=0.3)
    return el, wr


def body_pts(bw):
    s = bw
    return [(-24 * s, -12), (-46 * s, -2), (-62 * s, 10), (-69 * s, 30), (-63 * s, 64), (-55 * s, 100), (-47 * s, 165),
            (-50 * s, 236), (-24 * s, 244), (0, 246), (24 * s, 244), (50 * s, 236), (47 * s, 165), (55 * s, 100),
            (63 * s, 64), (69 * s, 30), (62 * s, 10), (46 * s, -2), (24 * s, -12)]


def draw_character(ctx, ch, P, light, t=0.0):
    """P: x,y,s, view, yaw,pitch,roll, lean, armL, armR, legs, E, shrug, breath, front_arms, lod, crop."""
    s = P.get("s", 1.0)
    lod = P.get("lod", 2 if s > 0.45 else 1 if s > 0.12 else 0)
    lw = P.get("lw", 2.0) / s
    bw = ch["build"]
    view = P.get("view", "front")
    ctx.save()
    ctx.translate(P["x"], P["y"])
    ctx.scale(s, s)
    br = math.sin(t * 2 * math.pi / P.get("breath_T", 4.2)) * P.get("breath", 1.0)
    shrug = P.get("shrug", 0.0)
    ctx.translate(0, 200)
    ctx.rotate(P.get("lean", 0.0))
    ctx.translate(0, -200)
    legs = P.get("legs")
    if legs:
        draw_legs(ctx, ch, legs, light, lw, lod, bw, t)
    sh_y = 22 - br * 1.6 - shrug * 9
    shL, shR = (-58 * bw, sh_y), (58 * bw, sh_y)
    armL = P.get("armL", {"a1": 6, "a2": 3})
    armR = P.get("armR", {"a1": -6, "a2": -3})
    behind = P.get("arms_behind", ())
    if "L" in behind:
        draw_arm(ctx, ch, shL, armL, light, lw, bw, lod, -1)
    if "R" in behind:
        draw_arm(ctx, ch, shR, armR, light, lw, bw, lod, 1)
    # neck
    roll = P.get("roll", 0.0) + P.get("iroll", 0.0)
    yaw, pitch = P.get("yaw", 0.0) + P.get("iyaw", 0.0), P.get("pitch", 0.0) + P.get("ipitch", 0.0)
    piv = (math.sin(roll) * 8 + yaw * 3, -46 - br * 0.6 - shrug * 3)
    hc = (piv[0] + math.sin(roll) * 44 + yaw * 4, piv[1] - math.cos(roll) * 44 + pitch * 6)
    skin = ch["skin"]
    nk = lambda: smooth_closed(ctx, [(-25 * bw, 2), (-21, -20), (hc[0] - 19, hc[1] + 40), (hc[0] - 6, hc[1] + 28),
                                     (hc[0] + 6, hc[1] + 28), (hc[0] + 19, hc[1] + 40), (21, -20), (25 * bw, 2)])
    shade(ctx, nk, skin, light, lw, shadow=0.5)
    if lod > 1 and view == "front":
        ctx.save(); ctx.new_path(); nk(); ctx.clip()
        g = cairo.LinearGradient(0, hc[1] + 40, 0, hc[1] + 70)
        g.add_color_stop_rgba(0, *light["shadow"], 0.55)
        g.add_color_stop_rgba(1, *light["shadow"], 0)
        ctx.set_source(g); ctx.paint()
        # sternocleidomastoids: behind each ear down to the notch
        for sgn in (1, -1):
            top = (hc[0] + sgn * 26 - yaw * 8, hc[1] + 30)
            soft_stroke(ctx, [top, ((top[0] + sgn * 5) * 0.5, (top[1] - 4) * 0.5), (sgn * 4, -3)], mul(skin, 0.6), 0.32, lw * 1.2)
        ctx.restore()
    # torso
    bp = body_pts(bw)
    bp = [(x * (1 + (0.012 * br if y < 120 else 0)), y + (-shrug * 7 if y < 40 and abs(x) > 30 else 0)) for x, y in bp]
    if ch["torn"]:
        hem = [(-51 * bw, 236), (-40 * bw, 248), (-30 * bw, 238), (-18 * bw, 250), (-6, 241), (8, 252), (22 * bw, 240), (36 * bw, 250), (51 * bw, 236)]
        bp = bp[:7] + hem + bp[12:]
    shade(ctx, lambda: smooth_closed(ctx, bp), ch["shirt"], light, lw, shadow=0.45)
    if lod > 1:
        fold = mul(ch["shirt"], 0.6)
        for sgn in (1, -1):
            soft_stroke(ctx, [(sgn * 50 * bw, 74), (sgn * 30, 104), (sgn * 18, 118)], fold, 0.35, lw)
            soft_stroke(ctx, [(sgn * 44 * bw, 168), (sgn * 26, 186), (sgn * 10, 192)], fold, 0.28, lw)
        if view == "front":
            _collar(ctx, ch, light, lw, bw)
        else:
            soft_stroke(ctx, [(0, 10), (0, 230)], fold, 0.25, lw)
    # head
    ctx.save()
    ctx.translate(*hc)
    ctx.rotate(roll)
    ctx.scale(1.08, 1.08)
    draw_head(ctx, ch, P.get("E", expr()), yaw, pitch, light, lw, lod, back=(view == "back"))
    ctx.restore()
    # front arms
    if "L" not in behind:
        draw_arm(ctx, ch, shL, armL, light, lw, bw, lod, -1)
    if "R" not in behind:
        draw_arm(ctx, ch, shR, armR, light, lw, bw, lod, 1)
    post = P.get("post")
    if post:
        post(ctx, lw)
    ctx.restore()
    return hc


def _collar(ctx, ch, light, lw, bw):
    c2 = ch["shirt2"]
    if ch["collar"] == "crew":
        ctx.new_path()
        ctx.move_to(-25 * bw, -4)
        ctx.curve_to(-18, 14, 18, 14, 25 * bw, -4)
        rgba(ctx, tint(c2, light))
        ctx.set_line_width(6)
        ctx.stroke_preserve()
        rgba(ctx, light.get("line"), 0.7)
        ctx.set_line_width(lw)
        ctx.stroke()
        if ch["torn"]:
            soft_stroke(ctx, [(10, 8), (14, 22), (8, 30)], mul(c2, 0.5), 0.6, lw)
    else:
        # flight suit V collar + zip + pocket
        for sgn in (1, -1):
            shade(ctx, lambda: smooth_closed(ctx, [(sgn * 22 * bw, -6), (sgn * 40 * bw, 4), (sgn * 30, 30), (sgn * 4, 44)]),
                  c2, light, lw, shadow=0.3)
            shade(ctx, lambda: (ctx.new_sub_path(), _rrect(ctx, sgn * 22 - 14 if sgn > 0 else -36, 70, 28, 34, 4)),
                  mul(ch["shirt"], 0.95), light, lw * 0.8, shadow=0.25, rim=0.3)
        soft_stroke(ctx, [(0, 44), (0, 236)], mul(c2, 0.5), 0.6, lw * 1.2)
        soft_stroke(ctx, [(-40, 60), (-40, 60.1)], (0, 0, 0), 0.0, lw)


def draw_legs(ctx, ch, legs, light, lw, lod, bw, t):
    mode = legs.get("mode", "stand")
    pants, shoes = ch["pants"], ch["shoes"]
    hips = [(-25 * bw, 236), (25 * bw, 236)]
    if mode == "kneel":
        k = legs.get("k", 1.0)  # 0 standing -> 1 kneeling, sitting back on the heels (body lowered by caller)
        gy = lerp(578, 340, k)
        soft_dot(ctx, 0, gy - 6, 120, (0, 0, 0), 0.35 * k)
        for i, sgn in enumerate((-1, 1)):
            hp = hips[i]
            kn = (sgn * lerp(27, 42, k) * bw, lerp(401, 316, k))
            an = (sgn * lerp(28, 46, k) * bw, lerp(561, 300, k))
            if k < 0.97:
                shade(ctx, lambda: capsule(ctx, kn, an, 15, 10), pants, light, lw)
            else:
                # shins + soles tucked behind, just visible beside the hips
                shade(ctx, lambda: capsule(ctx, (sgn * 52 * bw, 300), (sgn * 64 * bw, 270), 13, 10), mul(pants, 0.8), light, lw)
                shade(ctx, lambda: ellipse(ctx, sgn * 68 * bw, 262, 11, 16, sgn * 0.4), shoes, light, lw)
            r1 = lerp(16, 22, k)
            shade(ctx, lambda: capsule(ctx, hp, kn, lerp(22, 25, k), r1), pants, light, lw, shadow=0.45, union=True)
            if lod > 1:
                soft_dot(ctx, kn[0] - light["dir"][0] * 6, kn[1] - 6, r1 * 0.8, light["rim"], 0.18 * k)
                soft_stroke(ctx, [(kn[0] - 14, kn[1] - 2), (kn[0], kn[1] + 6), (kn[0] + 14, kn[1] - 2)], mul(pants, 0.55), 0.4, lw)
                soft_stroke(ctx, [(hp[0] - sgn * 4, hp[1] + 18), (kn[0] - sgn * 12, kn[1] - 14)], mul(pants, 0.6), 0.3, lw)
        return
    if mode == "sit_knees":
        for i, sgn in enumerate((-1, 1)):
            hp = hips[i]
            kn = (sgn * 30, 150)
            an = (sgn * 32, 330)
            shade(ctx, lambda: capsule(ctx, kn, an, 16, 11), pants, light, lw)
            shade(ctx, lambda: ellipse(ctx, an[0], an[1] + 10, 18, 11), shoes, light, lw)
        return
    phase = legs.get("phase", 0.0)
    run = mode == "run"
    for i, sgn in enumerate((-1, 1)):
        hp = hips[i]
        lift = max(0.0, math.sin(phase + (0 if i == 0 else math.pi))) if run else 0.0
        kn = (sgn * 27 * bw, 401 - 46 * lift)
        an = (sgn * 28 * bw, 561 - 120 * lift)
        if lift > 0.05 and legs.get("view") == "back":
            pass
        shade(ctx, lambda: capsule(ctx, kn, an, 15.5, 10.5), pants, light, lw)
        shade(ctx, lambda: capsule(ctx, hp, kn, 22, 16), pants, light, lw, shadow=0.45)
        if lod > 1:
            soft_stroke(ctx, [(kn[0] - 9, kn[1] - 6), (kn[0] + 2, kn[1] + 2), (kn[0] + 9, kn[1] - 4)], mul(pants, 0.55), 0.4, lw)
            soft_stroke(ctx, [(hp[0] - sgn * 8, hp[1] + 24), (kn[0] - sgn * 6, kn[1] - 40)], mul(pants, 0.6), 0.28, lw)
        # shoe (front view: toe toward camera)
        shade(ctx, lambda: smooth_closed(ctx, [(an[0] - 13, an[1] - 4), (an[0] + 13, an[1] - 4), (an[0] + 16, an[1] + 12),
                                                (an[0], an[1] + 18 - lift * 6), (an[0] - 16, an[1] + 12)]), shoes, light, lw)
        shade(ctx, lambda: capsule(ctx, (an[0], an[1] - 12), (an[0], an[1] - 2), 12, 12.5), mul(pants, 0.9), light, lw, shadow=0.3)
