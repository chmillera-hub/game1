"""Puppet drawing for Maya and Grandpa Abe with Cairo.

All face geometry is in units of the head radius R around the head centre.
A character's live state is a dict of floats (see state.py)."""
import math
import cairo

TAU = math.tau


def rgb(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def mix(c1, c2, t):
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def src(ctx, c):
    ctx.set_source_rgba(*c)


MAYA = dict(
    name="M", R=80.0, skin=rgb("#c68a5e"), skin_sh=rgb("#a86f48"), lip=rgb("#9c4c42"),
    hair=rgb("#24160f"), hair_hi=rgb("#3d281c"), iris=rgb("#3b2214"), iris_hi=rgb("#7a4a2a"),
    shirt=rgb("#e3a738"), shirt_sh=rgb("#b98226"), brow=rgb("#2a1a12"), eye_rx=0.205, eye_ry=0.24,
    iris_r=0.15, brow_w=0.075,
)
ABE = dict(
    name="A", R=84.0, skin=rgb("#b98060"), skin_sh=rgb("#9a6648"), lip=rgb("#8a4a40"),
    hair=rgb("#e9e4dc"), hair_hi=rgb("#ffffff"), iris=rgb("#4c6a86"), iris_hi=rgb("#8fb0c9"),
    shirt=rgb("#5c7a55"), shirt_sh=rgb("#45603f"), brow=rgb("#f1ede6"), eye_rx=0.16, eye_ry=0.16,
    iris_r=0.115, brow_w=0.11,
)


# --------------------------------------------------------------------------- body
def draw_body(ctx, C, st):
    R = C["R"]
    ctx.save()
    ctx.translate(st["bx"], st["by"])
    ctx.scale(R, R)
    br = st.get("breath", 0.0)
    if C["name"] == "M":
        # hoodie torso
        ctx.move_to(-0.32, 0.9)
        ctx.curve_to(-0.75, 1.0, -1.2, 1.25, -1.25, 1.75)
        ctx.line_to(-1.38 - br * 0.01, 4.2)
        ctx.line_to(1.38 + br * 0.01, 4.2)
        ctx.line_to(1.25, 1.75)
        ctx.curve_to(1.2, 1.25, 0.75, 1.0, 0.32, 0.9)
        ctx.close_path()
        src(ctx, C["shirt"]); ctx.fill()
        # neck
        src(ctx, C["skin_sh"])
        ctx.rectangle(-0.24, 0.55, 0.48, 0.5); ctx.fill()
        # hood folds around the neck
        src(ctx, C["shirt_sh"])
        ctx.move_to(-0.62, 0.98); ctx.curve_to(-0.4, 1.38, 0.4, 1.38, 0.62, 0.98)
        ctx.curve_to(0.45, 1.12, -0.45, 1.12, -0.62, 0.98); ctx.fill()
        ctx.set_line_width(0.07)
        ctx.move_to(-0.75, 0.98); ctx.curve_to(-0.5, 1.5, 0.5, 1.5, 0.75, 0.98); ctx.stroke()
        # drawstrings
        src(ctx, rgb("#f4e3c0"))
        ctx.set_line_width(0.045); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        sway = st.get("sway", 0.0)
        ctx.move_to(-0.18, 1.28); ctx.curve_to(-0.2, 1.6, -0.22 + sway, 1.8, -0.2 + sway, 2.05); ctx.stroke()
        ctx.move_to(0.18, 1.28); ctx.curve_to(0.2, 1.6, 0.22 + sway, 1.8, 0.2 + sway, 2.0); ctx.stroke()
        # pocket seam
        src(ctx, C["shirt_sh"]); ctx.set_line_width(0.04)
        ctx.move_to(-0.7, 3.1); ctx.curve_to(-0.3, 2.95, 0.3, 2.95, 0.7, 3.1); ctx.stroke()
    else:
        # shirt + cardigan
        ctx.move_to(-0.36, 0.92)
        ctx.curve_to(-0.8, 1.0, -1.25, 1.2, -1.3, 1.75)
        ctx.line_to(-1.42, 4.2); ctx.line_to(1.42, 4.2); ctx.line_to(1.3, 1.75)
        ctx.curve_to(1.25, 1.2, 0.8, 1.0, 0.36, 0.92); ctx.close_path()
        src(ctx, C["shirt"]); ctx.fill()
        src(ctx, C["skin_sh"])
        ctx.rectangle(-0.26, 0.55, 0.52, 0.5); ctx.fill()
        # cream shirt V
        src(ctx, rgb("#efe6d2"))
        ctx.move_to(-0.42, 0.95); ctx.line_to(0.42, 0.95); ctx.line_to(0.12, 2.4); ctx.line_to(-0.12, 2.4); ctx.close_path(); ctx.fill()
        src(ctx, rgb("#d8ccb2"))
        ctx.move_to(-0.36, 0.95); ctx.line_to(-0.05, 1.35); ctx.line_to(-0.2, 1.5); ctx.close_path(); ctx.fill()
        ctx.move_to(0.36, 0.95); ctx.line_to(0.05, 1.35); ctx.line_to(0.2, 1.5); ctx.close_path(); ctx.fill()
        # cardigan edges + buttons
        src(ctx, C["shirt_sh"]); ctx.set_line_width(0.06)
        ctx.move_to(-0.44, 0.98); ctx.line_to(-0.14, 2.5); ctx.line_to(-0.14, 4.2); ctx.stroke()
        ctx.move_to(0.44, 0.98); ctx.line_to(0.14, 2.5); ctx.line_to(0.14, 4.2); ctx.stroke()
        src(ctx, rgb("#c9b48a"))
        for y in (2.75, 3.3, 3.85):
            ctx.arc(-0.24, y, 0.055, 0, TAU); ctx.fill()
    ctx.restore()


# --------------------------------------------------------------------------- head
def face_path(ctx, C, turn):
    cx = turn * 0.07
    if C["name"] == "M":
        ctx.move_to(0, -1.02)
        ctx.curve_to(0.6, -1.02, 0.93, -0.6, 0.92, -0.08)
        ctx.curve_to(0.9, 0.42, 0.62 + cx, 0.88, 0.05 + cx, 1.0)
        ctx.curve_to(-0.62 + cx, 0.88, -0.9, 0.42, -0.92, -0.08)
        ctx.curve_to(-0.93, -0.6, -0.6, -1.02, 0, -1.02)
    else:
        ctx.move_to(0, -1.05)
        ctx.curve_to(0.62, -1.05, 0.95, -0.62, 0.95, -0.1)
        ctx.curve_to(0.95, 0.45, 0.7 + cx, 0.92, 0.05 + cx, 1.02)
        ctx.curve_to(-0.7 + cx, 0.92, -0.95, 0.45, -0.95, -0.1)
        ctx.curve_to(-0.95, -0.62, -0.62, -1.05, 0, -1.05)
    ctx.close_path()


def draw_head(ctx, C, st, mirror=False):
    R = C["R"]
    turn = st["turn"]
    ctx.save()
    ctx.translate(st["hx"], st["hy"])
    ctx.scale(R, R)
    # tilt around the neck
    ctx.translate(0, 0.85); ctx.rotate(st["tilt"]); ctx.translate(0, -0.85)
    if mirror:
        ctx.scale(-1, 1)

    if C["name"] == "M":
        _maya_hair_back(ctx, C, st)
    _ears(ctx, C, turn)
    face_path(ctx, C, turn)
    src(ctx, C["skin"]); ctx.fill_preserve()
    # soft shading on the far side
    ctx.save(); ctx.clip()
    sx = 1.0 if turn > 0 else -1.0
    gx0 = -sx * 1.45 + turn * 0.25
    g = cairo.RadialGradient(gx0, 0.1, 0.55, gx0, 0.1, 1.05)
    g.add_color_stop_rgba(0, *C["skin_sh"][:3], 0.38)
    g.add_color_stop_rgba(1, *C["skin_sh"][:3], 0.0)
    ctx.set_source(g); ctx.paint()
    ctx.restore()
    ctx.new_path()

    # blush
    bl = st.get("blush", 0.0)
    if bl > 0.01:
        for s in (-1, 1):
            ctx.save()
            ctx.translate(s * 0.52 + turn * 0.22, 0.34); ctx.scale(0.2, 0.11)
            ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
            ctx.set_source_rgba(0.88, 0.36, 0.32, 0.22 * bl); ctx.fill()

    if C["name"] == "A":
        _abe_lines(ctx, C, st)
    _eyes(ctx, C, st)
    _brows(ctx, C, st)
    _nose(ctx, C, st)
    if C["name"] == "A":
        _abe_beard(ctx, C, st)
    _mouth(ctx, C, st)
    if C["name"] == "A":
        _abe_mustache(ctx, C, st)
        _abe_hair(ctx, C, st)
        _glasses(ctx, C, st)
    else:
        _maya_hair_front(ctx, C, st)
    if st.get("tear", 0) > 0:
        _tear(ctx, C, st)
    ctx.restore()


def _ears(ctx, C, turn):
    for s in (-1, 1):
        vis = 1 - max(0, s * turn) * 1.6
        if vis <= 0.05:
            continue
        ctx.save()
        ctx.translate(s * (0.9 - max(0, -s * turn) * 0.08) + turn * 0.05, 0.08)
        ctx.scale(0.15 * vis, 0.22)
        ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
        src(ctx, C["skin_sh"]); ctx.fill()
        if C["name"] == "M":
            ctx.arc(s * 0.9 + turn * 0.05, 0.3, 0.035, 0, TAU)
            src(ctx, rgb("#f2c94c")); ctx.fill()


def eye_centers(C, turn):
    ex = 0.36
    out = []
    for s in (-1, 1):
        x = s * ex * (1 - 0.18 * max(0, s * turn)) + turn * 0.23
        w = 1 - 0.3 * max(0, s * turn)
        out.append((s, x, 0.02, w))
    return out


def _lid_curves(rx, ry, lid, lidb):
    # upper lid: line at y_l with corners lower than centre (arched)
    y_l = -ry + 2 * ry * max(-0.15, min(1.0, lid))
    k = 0.32 * ry * (1 - min(1, max(0, lid)))
    up = lambda x: y_l + k * (x / rx) ** 2 - (0.0 if lid < 0.98 else 0)
    y_b = ry - 2 * ry * max(0, min(0.6, lidb))
    lo = lambda x: y_b - 0.3 * ry * (x / rx) ** 2
    return up, lo


def _eyes(ctx, C, st):
    turn = st["turn"]
    gx, gy = st["gx"], st["gy"]
    for s, x, y, w in eye_centers(C, turn):
        rx = C["eye_rx"] * w; ry = C["eye_ry"]
        lid = st["lid"]
        if s == -1 and st.get("wink", 0) > 0:
            lid = max(lid, st["wink"])
        lid = max(lid, st["blink"])
        lidb = st["lidb"]
        lid = min(1.0, lid + max(0, gy) * 0.18)
        up, lo = _lid_curves(rx, ry, lid, lidb)
        ctx.save()
        ctx.translate(x, y)
        ctx.save(); ctx.scale(rx, ry); ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
        ctx.save()
        ctx.clip_preserve()
        src(ctx, rgb("#f7f2ea")); ctx.fill()
        # iris + pupil
        ix = gx * rx * 0.42 + turn * 0.02; iy = gy * ry * 0.35
        ir = C["iris_r"]
        src(ctx, C["iris"]); ctx.arc(ix, iy, ir, 0, TAU); ctx.fill()
        src(ctx, C["iris_hi"][:3] + (0.55,)); ctx.arc(ix, iy + ir * 0.25, ir * 0.62, 0, math.pi); ctx.fill()
        src(ctx, rgb("#0d0806")); ctx.arc(ix, iy, ir * (0.48 + st.get("pupil", 0) * 0.1), 0, TAU); ctx.fill()
        src(ctx, (1, 1, 1, 0.95)); ctx.arc(ix + ir * 0.38, iy - ir * 0.4, ir * 0.27, 0, TAU); ctx.fill()
        src(ctx, (1, 1, 1, 0.7)); ctx.arc(ix - ir * 0.35, iy + ir * 0.38, ir * 0.12, 0, TAU); ctx.fill()
        wet = st.get("wet", 0)
        if wet > 0.02:
            src(ctx, (0.85, 0.93, 1.0, 0.55 * wet))
            pts = [(xx / 10 * rx * 2 - rx) for xx in range(11)]
            ctx.move_to(pts[0], lo(pts[0]) - 0.012)
            for px in pts[1:]:
                ctx.line_to(px, lo(px) - 0.012)
            for px in reversed(pts):
                ctx.line_to(px, lo(px) - 0.045 * wet)
            ctx.close_path(); ctx.fill()
        # upper lid skin
        src(ctx, C["skin"])
        n = 12
        xs = [-rx * 1.05 + 2.1 * rx * i / n for i in range(n + 1)]
        ctx.move_to(xs[0], -ry * 1.6)
        for px in xs:
            ctx.line_to(px, up(px))
        ctx.line_to(xs[-1], -ry * 1.6); ctx.close_path(); ctx.fill()
        # crease shadow
        src(ctx, C["skin_sh"][:3] + (0.5,))
        ctx.move_to(xs[0], up(xs[0]) - 0.04)
        for px in xs:
            ctx.line_to(px, up(px) - 0.04)
        for px in reversed(xs):
            ctx.line_to(px, up(px))
        ctx.close_path(); ctx.fill()
        # lower lid skin
        src(ctx, C["skin"])
        ctx.move_to(xs[0], ry * 1.6)
        for px in xs:
            ctx.line_to(px, lo(px))
        ctx.line_to(xs[-1], ry * 1.6); ctx.close_path(); ctx.fill()
        ctx.restore()  # clip
        ctx.new_path()
        # lash line along the upper lid, clamped to the eye outline
        lw = 0.05 if C["name"] == "M" else 0.03
        src(ctx, rgb("#1a0f0a") if C["name"] == "M" else rgb("#4a3328"))
        ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        first = True
        for i in range(n + 1):
            px = -rx + 2 * rx * i / n
            lim = ry * math.sqrt(max(0, 1 - (px / rx) ** 2))
            py = max(-lim, min(lim, up(px)))
            if first:
                ctx.move_to(px, py); first = False
            else:
                ctx.line_to(px, py)
        ctx.stroke()
        if C["name"] == "M":
            # outer flick
            ox = s * rx
            ctx.move_to(ox * 0.92, up(ox * 0.92)); ctx.line_to(ox * 1.12, up(ox) - 0.06 * (1 - lid * 0.6))
            ctx.stroke()
        # faint lower line
        ctx.set_line_width(0.015)
        src(ctx, C["skin_sh"][:3] + (0.8,))
        for i in range(n + 1):
            px = -rx * 0.8 + 1.6 * rx * i / n
            lim = ry * math.sqrt(max(0, 1 - (px / rx) ** 2))
            py = min(lim, lo(px))
            (ctx.move_to if i == 0 else ctx.line_to)(px, py)
        ctx.stroke()
        ctx.restore()


def _brows(ctx, C, st):
    turn = st["turn"]
    raise_, tilt = st["brow"], st["btilt"]
    asym = st.get("basym", 0.0)
    src(ctx, C["brow"])
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for s, x, y, w in eye_centers(C, turn):
        r = raise_ + (asym if s == 1 else -asym * 0.3)
        base = -0.37 - r * 0.11 - (0.04 if C["name"] == "A" else 0)
        inner = (x - s * 0.13 * w, base - tilt * 0.1 + 0.015)
        outer = (x + s * 0.2 * w, base + tilt * 0.04 + 0.03)
        mid = ((inner[0] + outer[0]) / 2, min(inner[1], outer[1]) - 0.045 - max(0, tilt) * 0.0)
        ctx.set_line_width(C["brow_w"])
        ctx.move_to(*inner); ctx.curve_to(mid[0], mid[1], mid[0], mid[1], *outer); ctx.stroke()
        if C["name"] == "A":
            ctx.set_line_width(0.035)
            for k in range(3):
                tx = outer[0] - s * k * 0.05
                ctx.move_to(tx, outer[1] - 0.02); ctx.line_to(tx + s * 0.05, outer[1] - 0.07 + k * 0.02); ctx.stroke()


def _nose(ctx, C, st):
    turn = st["turn"]
    nx = turn * 0.3
    if C["name"] == "M":
        src(ctx, C["skin_sh"])
        ctx.set_line_width(0.035); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        d = 1 if turn >= 0 else -1
        ctx.move_to(nx + d * 0.02, 0.08); ctx.curve_to(nx + d * 0.08, 0.2, nx + d * 0.07, 0.27, nx + d * 0.02, 0.3)
        ctx.stroke()
        ctx.move_to(nx - 0.08, 0.3); ctx.curve_to(nx - 0.04, 0.34, nx + 0.04, 0.34, nx + 0.08, 0.3); ctx.stroke()
    else:
        ctx.save(); ctx.translate(nx, 0.24); ctx.scale(0.14, 0.12); ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
        src(ctx, mix(C["skin"], C["skin_sh"], 0.5)); ctx.fill()
        src(ctx, C["skin_sh"]); ctx.set_line_width(0.03)
        ctx.move_to(nx - 0.1, 0.3); ctx.curve_to(nx - 0.05, 0.36, nx + 0.05, 0.36, nx + 0.1, 0.3); ctx.stroke()


def _mouth(ctx, C, st):
    turn = st["turn"]
    cx = turn * 0.22
    cy = 0.53 if C["name"] == "M" else 0.6
    w = (0.36 if C["name"] == "M" else 0.32) * st["mw"]
    h = st["jaw"] * (0.27 if C["name"] == "M" else 0.22)
    s = st["smile"]
    cl = (cx - w / 2, cy - s * 0.085)
    cr = (cx + w / 2, cy - s * 0.085)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if h < 0.025:
        src(ctx, mix(C["lip"], (0.2, 0.08, 0.06, 1), 0.3))
        ctx.set_line_width(0.034)
        ctx.move_to(*cl); ctx.curve_to(cx - w * 0.2, cy + s * 0.07, cx + w * 0.2, cy + s * 0.07, *cr); ctx.stroke()
        # lower lip hint
        if C["name"] == "M":
            src(ctx, C["lip"][:3] + (0.55,)); ctx.set_line_width(0.03)
            ctx.move_to(cx - w * 0.22, cy + 0.07 + s * 0.02); ctx.curve_to(cx - 0.05, cy + 0.1, cx + 0.05, cy + 0.1, cx + w * 0.22, cy + 0.07 + s * 0.02)
            ctx.stroke()
        return
    top = cy - h * 0.22 + s * 0.03
    bot = cy + h + s * 0.04
    ctx.move_to(*cl)
    ctx.curve_to(cx - w * 0.25, top, cx + w * 0.25, top, *cr)
    ctx.curve_to(cx + w * 0.3, bot, cx - w * 0.3, bot, *cl)
    ctx.close_path()
    src(ctx, rgb("#3a1411")); ctx.fill_preserve()
    ctx.save(); ctx.clip()
    # teeth
    src(ctx, rgb("#f4efe6"))
    ctx.rectangle(cx - w * 0.4, top - 0.05, w * 0.8, min(h * 0.32, 0.055) + 0.05 + s * 0.01); ctx.fill()
    if h > 0.08:
        src(ctx, rgb("#c25b5b"))
        ctx.save(); ctx.translate(cx, bot - 0.01); ctx.scale(w * 0.32, h * 0.32); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    ctx.restore()
    ctx.new_path()
    src(ctx, C["lip"]); ctx.set_line_width(0.03)
    ctx.move_to(*cl); ctx.curve_to(cx - w * 0.25, top, cx + w * 0.25, top, *cr); ctx.stroke()
    ctx.set_line_width(0.045)
    ctx.move_to(cl[0] + w * 0.12, cl[1] + h * 0.4); ctx.curve_to(cx - w * 0.25, bot + 0.02, cx + w * 0.25, bot + 0.02, cr[0] - w * 0.12, cr[1] + h * 0.4)
    ctx.stroke()


def _tear(ctx, C, st):
    p = st["tear"]
    turn = st["turn"]
    s, x, y, w = eye_centers(C, turn)[0 if turn > 0 else 1]
    x0 = x + 0.05 * s; y0 = 0.22
    y1 = y0 + 0.55 * min(1, p)
    # wet streak
    ctx.set_source_rgba(0.85, 0.93, 1.0, 0.45)
    ctx.set_line_width(0.03)
    ctx.move_to(x0, y0); ctx.curve_to(x0 - 0.02, y0 + 0.15, x0 - 0.04, y1 - 0.1, x0 - 0.04, y1); ctx.stroke()
    if p < 1.4:
        ctx.set_source_rgba(0.8, 0.9, 1.0, 0.9)
        ty = y1
        ctx.move_to(x0 - 0.04, ty - 0.06)
        ctx.curve_to(x0 + 0.0, ty, x0 - 0.0, ty + 0.05, x0 - 0.04, ty + 0.05)
        ctx.curve_to(x0 - 0.08, ty + 0.05, x0 - 0.08, ty, x0 - 0.04, ty - 0.06)
        ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 0.9); ctx.arc(x0 - 0.05, ty + 0.015, 0.012, 0, TAU); ctx.fill()


def _maya_hair_back(ctx, C, st):
    src(ctx, C["hair"])
    t = st["turn"]
    for (x, y, r) in [(-0.85, -0.35, 0.36), (0.85, -0.35, 0.36), (-0.7, -0.8, 0.4), (0.7, -0.8, 0.4),
                      (-0.3, -1.05, 0.42), (0.3, -1.05, 0.42), (-0.95, 0.15, 0.28), (0.95, 0.15, 0.28),
                      (0.0, -1.1, 0.4)]:
        ctx.arc(x + t * 0.05, y, r, 0, TAU); ctx.fill()
    # bun
    bx = 0.12 + t * 0.12; by = -1.42 + st.get("bun", 0)
    ctx.arc(bx, by, 0.42, 0, TAU); ctx.fill()
    src(ctx, C["hair_hi"])
    ctx.set_line_width(0.035)
    for a in range(5):
        ang = a * 1.25 + 0.4
        ctx.arc(bx + 0.2 * math.cos(ang), by + 0.2 * math.sin(ang), 0.1, ang, ang + 2.5); ctx.stroke()
    # scrunchie
    src(ctx, rgb("#c0584b"))
    ctx.save(); ctx.translate(bx - 0.02, by + 0.38); ctx.scale(0.3, 0.09); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()


def _maya_hair_front(ctx, C, st):
    t = st["turn"]
    src(ctx, C["hair"])
    px = 0.15 + t * 0.25  # part position
    ctx.move_to(-0.96, -0.05)
    ctx.curve_to(-1.0, -0.75, -0.6, -1.12, 0, -1.1)
    ctx.curve_to(0.6, -1.12, 1.0, -0.75, 0.96, -0.05)
    ctx.curve_to(0.9, -0.35, 0.78, -0.55, 0.6, -0.62)
    ctx.curve_to(0.45, -0.66, px + 0.2, -0.74, px, -0.8)
    ctx.curve_to(px - 0.25, -0.66, -0.4, -0.66, -0.62, -0.58)
    ctx.curve_to(-0.8, -0.5, -0.9, -0.3, -0.96, -0.05)
    ctx.close_path(); ctx.fill()
    # loose curls at the temples
    src(ctx, C["hair"]); ctx.set_line_width(0.06); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    sway = st.get("sway", 0.0) * 0.6
    for s in (-1, 1):
        x0 = s * 0.82 + t * 0.06
        ctx.move_to(x0, -0.35)
        ctx.curve_to(x0 + s * 0.12 + sway, -0.1, x0 - s * 0.06 + sway, 0.08, x0 + s * 0.06 + sway, 0.3)
        ctx.stroke()
    src(ctx, C["hair_hi"]); ctx.set_line_width(0.03)
    ctx.move_to(-0.5, -0.95); ctx.curve_to(-0.2, -1.04, 0.1, -1.04, 0.3, -0.98); ctx.stroke()


def _abe_hair(ctx, C, st):
    t = st["turn"]
    src(ctx, C["hair"])
    for s in (-1, 1):
        vis = 1 - max(0, s * t) * 1.2
        if vis < 0.1:
            continue
        x = s * 0.86 + t * 0.04
        for (dx, dy, r) in [(0, -0.38, 0.2), (s * 0.06, -0.15, 0.18), (s * -0.05, -0.55, 0.16)]:
            ctx.arc(x + dx, dy, r * vis, 0, TAU); ctx.fill()
    ctx.set_line_width(0.035); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(4):
        x = -0.3 + k * 0.18 + t * 0.1
        ctx.move_to(x, -1.0); ctx.curve_to(x + 0.06, -1.14, x + 0.16, -1.15, x + 0.2, -1.08); ctx.stroke()


def _abe_lines(ctx, C, st):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    src(ctx, C["skin_sh"][:3] + (0.7,))
    ctx.set_line_width(0.022)
    t = st["turn"]
    fr = 0.25 + max(0, st["brow"]) * 0.75
    for k in range(3):
        y = -0.68 - k * 0.09
        ctx.move_to(-0.42 + t * 0.15, y); ctx.curve_to(-0.15, y - 0.03 * fr, 0.15, y - 0.03 * fr, 0.42 + t * 0.15, y)
        ctx.set_source_rgba(*C["skin_sh"][:3], 0.25 + 0.5 * fr); ctx.stroke()
    # crow's feet when the cheeks lift
    cr = min(1, st["lidb"] * 2.5)
    if cr > 0.05:
        ctx.set_source_rgba(*C["skin_sh"][:3], 0.8 * cr)
        for s, x, y, w in eye_centers(C, t):
            ox = x + s * C["eye_rx"] * w * 1.25
            for k in (-1, 0, 1):
                ctx.move_to(ox, y + k * 0.06); ctx.line_to(ox + s * 0.09, y + k * 0.09); ctx.stroke()


def _abe_beard(ctx, C, st):
    t = st["turn"]
    j = st["jaw"] * 0.12
    src(ctx, C["hair"])
    ctx.move_to(-0.9, 0.12)
    ctx.curve_to(-0.86, 0.6, -0.55, 1.12 + j, 0.04 + t * 0.07, 1.2 + j)
    ctx.curve_to(0.6, 1.12 + j, 0.9, 0.6, 0.9, 0.12)
    ctx.curve_to(0.75, 0.42, 0.45, 0.5, 0.25 + t * 0.2, 0.52)
    ctx.curve_to(0.1, 0.8 + j, -0.1, 0.8 + j, -0.25 + t * 0.2, 0.52)
    ctx.curve_to(-0.45, 0.5, -0.75, 0.42, -0.9, 0.12)
    ctx.close_path(); ctx.fill()
    src(ctx, rgb("#d4cdc2")); ctx.set_line_width(0.02)
    for k in range(5):
        x = -0.4 + k * 0.2 + t * 0.1
        ctx.move_to(x, 0.85 + j); ctx.line_to(x + 0.03, 1.0 + j); ctx.stroke()


def _abe_mustache(ctx, C, st):
    t = st["turn"]; cx = t * 0.22
    s = st["smile"]
    src(ctx, C["hair"])
    ctx.move_to(cx, 0.42)
    ctx.curve_to(cx + 0.15, 0.36, cx + 0.3, 0.42, cx + 0.32, 0.55 - s * 0.05)
    ctx.curve_to(cx + 0.2, 0.52 - s * 0.03, cx + 0.1, 0.55, cx, 0.53)
    ctx.curve_to(cx - 0.1, 0.55, cx - 0.2, 0.52 - s * 0.03, cx - 0.32, 0.55 - s * 0.05)
    ctx.curve_to(cx - 0.3, 0.42, cx - 0.15, 0.36, cx, 0.42)
    ctx.fill()


def _glasses(ctx, C, st):
    t = st["turn"]
    ec = eye_centers(C, t)
    ctx.set_line_width(0.035)
    for s, x, y, w in ec:
        ctx.save(); ctx.translate(x, y + 0.01); ctx.scale(0.25 * w, 0.22); ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
        ctx.set_source_rgba(0.75, 0.85, 0.95, 0.12); ctx.fill_preserve()
        src(ctx, rgb("#5b4636")); ctx.stroke()
        # glint
        ctx.set_source_rgba(1, 1, 1, 0.35); ctx.set_line_width(0.02)
        ctx.arc(x - 0.05, y - 0.04, 0.15 * w, 3.6, 4.4); ctx.stroke(); ctx.set_line_width(0.035)
    src(ctx, rgb("#5b4636"))
    ctx.move_to(ec[0][1] + 0.25 * ec[0][3], 0.0); ctx.curve_to(ec[0][1] + 0.3, -0.06, ec[1][1] - 0.3, -0.06, ec[1][1] - 0.25 * ec[1][3], 0.0)
    ctx.stroke()


# --------------------------------------------------------------------------- arms
def _ik(sh, hand, l1, l2, bend):
    dx, dy = hand[0] - sh[0], hand[1] - sh[1]
    d = math.hypot(dx, dy)
    d = min(d, l1 + l2 - 1e-3)
    a = math.atan2(dy, dx)
    cosb = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d + 1e-9)
    b = math.acos(max(-1, min(1, cosb)))
    c1 = (sh[0] + l1 * math.cos(a + b), sh[1] + l1 * math.sin(a + b))
    c2 = (sh[0] + l1 * math.cos(a - b), sh[1] + l1 * math.sin(a - b))
    lower = c1 if c1[1] > c2[1] else c2
    other = c2 if lower is c1 else c1
    # mostly hang the elbow down, nudged outward
    return lower if abs(lower[1] - other[1]) > 4 else (c1 if (c1[0] - sh[0]) * bend > 0 else c2)


def draw_arms(ctx, C, st):
    R = C["R"]
    for side in ("L", "R"):
        s = -1 if side == "L" else 1
        sh = (st["bx"] + s * 1.08 * R, st["by"] + 1.6 * R)
        hand = (st[side + "x"], st[side + "y"])
        bend = -s  # elbows out
        el = _ik(sh, hand, 1.25 * R, 1.2 * R, bend)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        src(ctx, C["shirt_sh"]); ctx.set_line_width(0.5 * R)
        ctx.move_to(*sh); ctx.line_to(*el); ctx.line_to(*hand); ctx.stroke()
        src(ctx, C["shirt"]); ctx.set_line_width(0.4 * R)
        ctx.move_to(*sh); ctx.line_to(*el); ctx.line_to(*hand); ctx.stroke()
        # cuff
        src(ctx, C["shirt_sh"])
        ang = math.atan2(hand[1] - el[1], hand[0] - el[0])
        ctx.arc(hand[0] - math.cos(ang) * 0.05 * R, hand[1] - math.sin(ang) * 0.05 * R, 0.22 * R, 0, TAU); ctx.fill()
        _hand(ctx, C, hand, ang, st.get(side + "h", "rest"), R, s)


def _hand(ctx, C, p, ang, kind, R, s):
    ctx.save()
    ctx.translate(*p)
    ctx.rotate(ang)
    ctx.scale(R, R)
    src(ctx, C["skin"])
    if kind == "fist":
        ctx.save(); ctx.scale(0.24, 0.2); ctx.arc(0.6, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
        src(ctx, C["skin_sh"]); ctx.set_line_width(0.025)
        for k in range(3):
            ctx.move_to(0.18 + k * 0.07, -0.15); ctx.line_to(0.18 + k * 0.07, -0.02); ctx.stroke()
    else:
        ctx.save(); ctx.scale(0.27, 0.2); ctx.arc(0.6, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
        # fingers
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(0.075)
        spread = 0.25 if kind == "open" else 0.12
        ln = 0.2 if kind != "point" else 0.14
        for k in range(4):
            a = (k - 1.5) * spread * 0.5
            l = ln + (0.1 if (kind == "point" and k == 1) else 0)
            ctx.move_to(0.32, (k - 1.5) * 0.06)
            ctx.line_to(0.32 + l * math.cos(a), (k - 1.5) * 0.06 + l * math.sin(a))
            src(ctx, C["skin"]); ctx.stroke()
        ctx.move_to(0.15, -0.14 * s * -1); ctx.line_to(0.3, -0.24 * s * -1); ctx.stroke()
    ctx.restore()
