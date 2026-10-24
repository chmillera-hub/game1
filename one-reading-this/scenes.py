"""Kitchen set, props, scripture cards, subtitles, titles."""
import math
import random
import cairo
from chars import rgb, src, MAYA, ABE, draw_body, draw_head, draw_arms

W, H = 720, 1280
TAU = math.tau
SANS = "Inter"
SERIF = "Liberation Serif"

_rain_seed = random.Random(3)
RAIN = [(_rain_seed.uniform(40, 360), _rain_seed.uniform(0, 1), _rain_seed.uniform(0.6, 1.0)) for _ in range(46)]
DROPS = [(_rain_seed.uniform(70, 330), _rain_seed.uniform(140, 460), _rain_seed.uniform(2, 5), _rain_seed.uniform(0, 1)) for _ in range(26)]
CITY = [(_rain_seed.uniform(60, 340), _rain_seed.uniform(330, 450), _rain_seed.uniform(3, 9),
         _rain_seed.choice(["#f2b45a", "#e88a4a", "#9fc3e8", "#f5d68a"])) for _ in range(24)]


def lin(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *c)
    return g


def rad(ctx, x, y, r0, r1, stops):
    g = cairo.RadialGradient(x, y, r0, x, y, r1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *c)
    return g


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


# ----------------------------------------------------------------- kitchen
def draw_window(ctx, S):
    x0, y0, x1, y1 = 60, 130, 340, 470
    ctx.save()
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0); ctx.clip()
    ctx.set_source(lin(ctx, 0, y0, 0, y1, [(0, rgb("#0b1424")), (1, rgb("#1b2b44"))])); ctx.paint()
    # distant city lights
    for (x, y, r, c) in CITY:
        ctx.set_source(rad(ctx, x, y, 0, r * 2.2, [(0, rgb(c, 0.7)), (1, rgb(c, 0.0))]))
        ctx.arc(x, y, r * 2.2, 0, TAU); ctx.fill()
    # rooftops
    src(ctx, rgb("#0a111d"))
    ctx.move_to(x0, 440); ctx.line_to(110, 410); ctx.line_to(150, 425); ctx.line_to(150, 395); ctx.line_to(210, 395)
    ctx.line_to(210, 420); ctx.line_to(270, 405); ctx.line_to(340, 430); ctx.line_to(340, 470); ctx.line_to(x0, 470); ctx.fill()
    # rain
    t = S["t"]; inten = S["rain"]
    ctx.set_line_width(1.6); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    n = int(len(RAIN) * inten)
    for i, (x, ph, sp) in enumerate(RAIN[:n]):
        yy = y0 + ((ph + t * 1.25 * sp) % 1.0) * (y1 - y0 + 60) - 30
        ctx.set_source_rgba(0.72, 0.82, 0.95, 0.35)
        ctx.move_to(x, yy); ctx.line_to(x - 4, yy + 22); ctx.stroke()
    # drops on the glass sliding slowly
    for (x, y, r, ph) in DROPS[:int(len(DROPS) * (0.4 + 0.6 * inten))]:
        yy = y + ((t * 6 * r + ph * 200) % 120)
        if yy > y1:
            continue
        ctx.set_source_rgba(0.8, 0.88, 1, 0.35); ctx.arc(x, yy, r, 0, TAU); ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 0.5); ctx.arc(x - r * 0.3, yy - r * 0.3, r * 0.35, 0, TAU); ctx.fill()
    # mirror: the glass becomes a reflection of Maya
    m = S.get("mirror", 0)
    if m > 0:
        ctx.set_source_rgba(0.75, 0.82, 0.9, 0.55 * m); ctx.paint()
        ctx.push_group()
        st = dict(S["M"]); st["hx"], st["hy"] = 200, 330; st["bx"], st["by"] = 200, 330
        st["turn"] = -0.15; st["gx"] = -0.1; st["gy"] = 0.0; st["tilt"] = 0.0
        draw_body(ctx, MAYA, st)
        draw_head(ctx, MAYA, st, mirror=True)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(0.75 * m)
        ctx.set_source(lin(ctx, x0, y0, x1, y1, [(0, (1, 1, 1, 0.35 * m)), (0.4, (1, 1, 1, 0.0)), (0.55, (1, 1, 1, 0.18 * m)), (0.7, (1, 1, 1, 0))]))
        ctx.paint()
    ctx.restore()
    # frame
    src(ctx, rgb("#e7dcc8"))
    ctx.set_line_width(14); ctx.rectangle(x0, y0, x1 - x0, y1 - y0); ctx.stroke()
    ctx.set_line_width(8)
    ctx.move_to((x0 + x1) / 2, y0); ctx.line_to((x0 + x1) / 2, y1); ctx.stroke()
    ctx.move_to(x0, (y0 + y1) / 2 - 20); ctx.line_to(x1, (y0 + y1) / 2 - 20); ctx.stroke()
    # sill + plant
    src(ctx, rgb("#d9cbb2")); ctx.rectangle(x0 - 22, y1 + 4, x1 - x0 + 44, 16); ctx.fill()
    src(ctx, rgb("#b5643f")); ctx.move_to(268, y1 + 4); ctx.line_to(304, y1 + 4); ctx.line_to(300, y1 - 26); ctx.line_to(272, y1 - 26); ctx.fill()
    src(ctx, rgb("#4f8a4c"))
    for a in (-0.7, -0.25, 0.2, 0.6):
        ctx.save(); ctx.translate(286, y1 - 26); ctx.rotate(a); ctx.scale(7, 22); ctx.arc(0, -1, 1, 0, TAU); ctx.restore(); ctx.fill()
    if S["beat"] >= 48:
        ctx.set_source_rgba(0.98, 0.85, 0.35, 1); ctx.arc(292, y1 - 70, 7, 0, TAU); ctx.fill()
        src(ctx, rgb("#4f8a4c")); ctx.set_line_width(2.5); ctx.move_to(288, y1 - 30); ctx.line_to(292, y1 - 64); ctx.stroke()


def draw_kitchen_back(ctx, S):
    ctx.set_source(lin(ctx, 0, 0, 0, 900, [(0, rgb("#1f2b41")), (1, rgb("#2d3b55"))]))
    ctx.rectangle(0, 0, W, 900); ctx.fill()
    # wallpaper stripes
    ctx.set_source_rgba(1, 1, 1, 0.025)
    for x in range(0, W, 48):
        ctx.rectangle(x, 0, 18, 900); ctx.fill()
    # lamp glow on the wall
    ctx.set_source(rad(ctx, 360, 300, 20, 560, [(0, (1.0, 0.78, 0.45, 0.42)), (0.5, (1.0, 0.7, 0.4, 0.12)), (1, (1, 0.7, 0.4, 0))]))
    ctx.rectangle(0, 0, W, 900); ctx.fill()
    draw_window(ctx, S)
    # clock (near midnight)
    cx, cy = 470, 175
    src(ctx, rgb("#efe5d2")); ctx.arc(cx, cy, 34, 0, TAU); ctx.fill()
    src(ctx, rgb("#6b5643")); ctx.set_line_width(4); ctx.arc(cx, cy, 34, 0, TAU); ctx.stroke()
    mins = 52 + S["t"] / 60.0
    for ang, l, w in ((((11 + mins / 60) / 12) * TAU, 16, 4), ((mins / 60) * TAU, 26, 2.5)):
        ctx.set_line_width(w); ctx.move_to(cx, cy); ctx.line_to(cx + l * math.sin(ang), cy - l * math.cos(ang)); ctx.stroke()
    # photograph by the door
    src(ctx, rgb("#5a4030")); ctx.rectangle(572, 262, 88, 108); ctx.fill()
    ctx.set_source(lin(ctx, 0, 270, 0, 362, [(0, rgb("#e8d3b0")), (1, rgb("#c9a986"))])); ctx.rectangle(580, 270, 72, 92); ctx.fill()
    src(ctx, rgb("#7a5a48")); ctx.arc(616, 304, 15, 0, TAU); ctx.fill()
    src(ctx, rgb("#a7c4c9")); ctx.move_to(592, 362); ctx.curve_to(596, 330, 636, 330, 640, 362); ctx.fill()
    src(ctx, rgb("#3b2a20")); ctx.arc(616, 296, 16, math.pi, TAU); ctx.fill()
    # door edge
    src(ctx, rgb("#4a3324")); ctx.rectangle(684, 120, 40, 790); ctx.fill()
    src(ctx, rgb("#d9b46a")); ctx.arc(696, 560, 6, 0, TAU); ctx.fill()
    # pendant lamp
    src(ctx, rgb("#11161f")); ctx.set_line_width(3); ctx.move_to(360, 0); ctx.line_to(360, 150); ctx.stroke()
    ctx.set_source(rad(ctx, 360, 225, 0, 90, [(0, (1, 0.9, 0.6, 0.8)), (1, (1, 0.8, 0.5, 0))]))
    ctx.arc(360, 225, 90, 0, TAU); ctx.fill()
    src(ctx, rgb("#c96f3f")); ctx.move_to(322, 150); ctx.line_to(398, 150); ctx.line_to(428, 212); ctx.line_to(292, 212); ctx.close_path(); ctx.fill()
    src(ctx, rgb("#ffe7b0")); ctx.save(); ctx.translate(360, 213); ctx.scale(66, 8); ctx.arc(0, 0, 1, 0, math.pi); ctx.restore(); ctx.fill()


def draw_table(ctx, S):
    ctx.set_source(lin(ctx, 0, 870, 0, 1012, [(0, rgb("#8a5634")), (1, rgb("#6c3f25"))]))
    ctx.rectangle(-10, 870, W + 20, 142); ctx.fill()
    ctx.set_source(rad(ctx, 360, 930, 10, 420, [(0, (1, 0.8, 0.5, 0.28)), (1, (1, 0.8, 0.5, 0))]))
    ctx.rectangle(-10, 870, W + 20, 142); ctx.fill()
    ctx.set_source_rgba(0.25, 0.12, 0.05, 0.25); ctx.set_line_width(2)
    for i, y in enumerate((890, 922, 958, 990)):
        ctx.move_to(-10, y); ctx.curve_to(200, y + 6 * math.sin(i), 500, y - 5, W + 10, y + 3); ctx.stroke()
    src(ctx, rgb("#4c2b18")); ctx.rectangle(-10, 1010, W + 20, 24); ctx.fill()
    ctx.set_source(lin(ctx, 0, 1034, 0, H, [(0, rgb("#3a2215")), (1, rgb("#22140c"))])); ctx.rectangle(-10, 1034, W + 20, H - 1034 + 10); ctx.fill()


def draw_book(ctx):
    x, y = 160, 918
    ctx.save(); ctx.translate(x, y)
    src(ctx, rgb("#5b2a22")); ctx.move_to(-108, 6); ctx.line_to(108, 6); ctx.line_to(116, 30); ctx.line_to(-116, 30); ctx.close_path(); ctx.fill()
    for s in (-1, 1):
        src(ctx, rgb("#f3ead6"))
        ctx.move_to(0, -6); ctx.curve_to(s * 40, -16, s * 80, -14, s * 104, -8); ctx.line_to(s * 110, 22); ctx.curve_to(s * 80, 16, s * 40, 16, 0, 24); ctx.close_path(); ctx.fill()
        ctx.set_source_rgba(0.35, 0.28, 0.2, 0.45); ctx.set_line_width(2)
        for k in range(4):
            yy = -4 + k * 6
            ctx.move_to(s * 14, yy + 2); ctx.line_to(s * (86 - k * 3), yy); ctx.stroke()
    ctx.set_source_rgba(0.4, 0.3, 0.2, 0.5); ctx.set_line_width(1.5); ctx.move_to(0, -6); ctx.line_to(0, 24); ctx.stroke()
    ctx.restore()


def draw_mug(ctx, x, y, col, steam, t, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    src(ctx, col)
    ctx.move_to(-20, -40); ctx.line_to(20, -40); ctx.line_to(18, 0); ctx.curve_to(18, 6, -18, 6, -18, 0); ctx.close_path(); ctx.fill()
    ctx.set_line_width(6); ctx.arc(22, -22, 10, -1.3, 1.3); ctx.stroke()
    src(ctx, rgb("#5a3418")); ctx.save(); ctx.translate(0, -40); ctx.scale(20, 5); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.18); ctx.rectangle(-14, -36, 6, 30); ctx.fill()
    if steam > 0.02:
        ctx.set_line_width(3); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in (-1, 1):
            ph = t * 1.6 + k
            ctx.set_source_rgba(1, 1, 1, 0.22 * steam)
            ctx.move_to(k * 6, -48)
            ctx.curve_to(k * 6 + 8 * math.sin(ph), -62, k * 6 - 8 * math.sin(ph + 1), -76, k * 6 + 4 * math.sin(ph + 2), -92)
            ctx.stroke()
    ctx.restore()


def draw_candle(ctx, x, y, t):
    ctx.set_source(rad(ctx, x, y - 34, 0, 120, [(0, (1, 0.8, 0.4, 0.35)), (1, (1, 0.7, 0.3, 0))]))
    ctx.arc(x, y - 34, 120, 0, TAU); ctx.fill()
    ctx.set_source_rgba(0.85, 0.9, 0.95, 0.35); rrect(ctx, x - 20, y - 46, 40, 48, 8); ctx.fill()
    src(ctx, rgb("#f1e7d0")); ctx.rectangle(x - 12, y - 32, 24, 32); ctx.fill()
    fl = 1 + 0.08 * math.sin(t * 13) + 0.05 * math.sin(t * 29)
    src(ctx, rgb("#ffcf6a")); ctx.save(); ctx.translate(x, y - 42); ctx.scale(6, 11 * fl); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    src(ctx, rgb("#fff6d6")); ctx.save(); ctx.translate(x, y - 40); ctx.scale(2.5, 5 * fl); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()


MUGC = {"M": rgb("#d9534f"), "A": rgb("#3f7fa6")}


def draw_kitchen(ctx, S):
    draw_kitchen_back(ctx, S)
    t = S["t"]
    M, A = S["M"], S["A"]
    for C, st in ((MAYA, M), (ABE, A)):
        if st["present"]:
            draw_body(ctx, C, st)
            draw_head(ctx, C, st)
    draw_table(ctx, S)
    draw_book(ctx)
    draw_candle(ctx, *S["candle"], t)
    from state import MUG_SPOT
    if S["mugs_on"]:
        for name, C, st in (("M", MAYA, M), ("A", ABE, A)):
            if not S["mug_placed"]:
                continue
            if st["hold"] > 0.5 and st["present"]:
                continue
            draw_mug(ctx, *MUG_SPOT[name], MUGC[name], S["steam"], t + (2 if name == "A" else 0))
    for name, C, st in (("M", MAYA, M), ("A", ABE, A)):
        if not st["present"]:
            continue
        if st["carry"]:
            draw_mug(ctx, st["Lx"] + 6, st["Ly"] + 18, MUGC["M"], 1.0, t)
            draw_mug(ctx, st["Rx"] - 6, st["Ry"] + 18, MUGC["A"], 1.0, t + 2)
        elif st["hold"] > 0.5 and S["mugs_on"] and (name == "A" or S["mug_placed"]):
            draw_mug(ctx, st["Rx"] + 4, st["Ry"] + 20, MUGC[name], S["steam"], t)
        draw_arms(ctx, C, st)
    # warm light cone
    ctx.set_source(lin(ctx, 0, 210, 0, 900, [(0, (1, 0.85, 0.55, 0.10)), (1, (1, 0.85, 0.55, 0.0))]))
    ctx.move_to(300, 212); ctx.line_to(420, 212); ctx.line_to(700, 900); ctx.line_to(20, 900); ctx.close_path(); ctx.fill()


# ----------------------------------------------------------------- overlays
def wrap(ctx, words, width):
    lines, cur, cw = [], [], 0
    space = ctx.text_extents(" ").x_advance
    for w in words:
        ww = ctx.text_extents(w).x_advance
        if cur and cw + space + ww > width:
            lines.append(cur); cur = [w]; cw = ww
        else:
            cw = cw + (space if cur else 0) + ww; cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def draw_subtitle(ctx, S):
    sub = S.get("sub")
    if not sub:
        return
    spk, text, age = sub
    italic = spk == "N"
    ctx.select_font_face(SANS, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    fs = 37
    ctx.set_font_size(fs)
    lines = wrap(ctx, text.split(), 630)
    lh = fs * 1.28
    label = {"M": "MAYA", "A": "ABE", "N": ""}[spk]
    lab_h = 30 if label else 0
    box_h = lh * len(lines) + 30 + lab_h
    y0 = 1222 - box_h
    ctx.set_source_rgba(0.04, 0.03, 0.05, 0.62)
    rrect(ctx, 22, y0, W - 44, box_h, 20); ctx.fill()
    y = y0 + 18
    if label:
        ctx.select_font_face(SANS, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(22)
        col = rgb("#f2b642") if spk == "M" else rgb("#9fd18f")
        src(ctx, col)
        ext = ctx.text_extents(label)
        ctx.move_to(W / 2 - ext.x_advance / 2, y + 20); ctx.show_text(label)
        y += lab_h
        ctx.select_font_face(SANS, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    else:
        ctx.select_font_face(SANS, cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(fs)
    for ln in lines:
        s = " ".join(ln)
        ext = ctx.text_extents(s)
        x = W / 2 - ext.x_advance / 2
        ctx.move_to(x, y + fs)
        ctx.text_path(s)
        ctx.set_source_rgba(0, 0, 0, 0.8); ctx.set_line_width(5); ctx.stroke_preserve()
        src(ctx, rgb("#e6e0ff") if italic else (1, 1, 1, 1)); ctx.fill()
        y += lh


def draw_card(ctx, S):
    cd = S.get("card")
    if not cd:
        return
    ref, before, name, after, mode = cd["c"]
    a = cd["a"]
    sub = cd["sub"] if cd["has_sub"] else 0
    ctx.push_group()
    x0, w = 34, W - 68
    pad = 26
    ctx.select_font_face(SERIF, cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
    fs = 34
    ctx.set_font_size(fs)
    rep = "the one reading this"
    if ref == "THE EXPERIMENT":
        tokens = [("Every time the text says", "n"), ("Christ", "name"), ("or", "n"), ("Jesus,", "name"), ("read it as:", "n")]
        words = []
        for tx, kind in tokens:
            for wd in tx.split():
                words.append((wd, kind))
    else:
        words = [(wd, "n") for wd in before.split()]
        if cd["has_sub"] and sub > 0:
            words.append((name, "name"))
            r = rep if before.strip() else "The one reading this"
            for wd in r.split():
                words.append((wd, "rep"))
        else:
            hl = "gold" if name in ("You", "I", "me") else "name"
            words.append((name, hl))
        aw = after.split()
        if aw and aw[0] in (".", ",") or (aw and not after.startswith(" ")):
            # glue punctuation to the previous token
            last = words[-1]; words[-1] = (last[0] + aw[0], last[1]); aw = aw[1:]
        words += [(wd, "n") for wd in aw]
    # layout
    space = ctx.text_extents(" ").x_advance
    lines, cur, cw = [], [], 0
    maxw = w - 2 * pad
    for wd, kind in words:
        if kind == "rep" and ref == "THE EXPERIMENT":
            continue
        ww = ctx.text_extents(wd).x_advance
        if cur and cw + space + ww > maxw:
            lines.append(cur); cur = []; cw = 0
        cur.append((wd, kind, ww)); cw += ww + space
    if cur:
        lines.append(cur)
    lh = fs * 1.3
    extra = 74 if ref == "THE EXPERIMENT" else 0
    h = 62 + lh * len(lines) + 22 + extra
    y0 = 52
    ctx.set_source_rgba(0, 0, 0, 0.35); rrect(ctx, x0 + 4, y0 + 8, w, h, 18); ctx.fill()
    ctx.set_source(lin(ctx, 0, y0, 0, y0 + h, [(0, rgb("#f6ead0")), (1, rgb("#e9d7b2"))])); rrect(ctx, x0, y0, w, h, 18); ctx.fill()
    src(ctx, rgb("#b8955c")); ctx.set_line_width(2); rrect(ctx, x0 + 8, y0 + 8, w - 16, h - 16, 12); ctx.stroke()
    ctx.select_font_face(SANS, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(20); src(ctx, rgb("#8a6232"))
    ext = ctx.text_extents(ref)
    ctx.move_to(W / 2 - ext.x_advance / 2, y0 + 40); ctx.show_text(ref)
    y = y0 + 62
    strike = min(1, sub / 0.4) if sub > 0 else 0
    reveal = max(0, (sub - 0.4) * 26)
    rep_i = 0
    for ln in lines:
        tw = sum(x[2] for x in ln) + space * (len(ln) - 1)
        x = W / 2 - tw / 2
        for wd, kind, ww in ln:
            ctx.select_font_face(SERIF, cairo.FONT_SLANT_ITALIC,
                                 cairo.FONT_WEIGHT_BOLD if kind in ("name", "rep", "gold") else cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(fs)
            ctx.move_to(x, y + fs)
            if kind == "name":
                src(ctx, (0.45, 0.16, 0.1, 1 - 0.55 * strike)); ctx.show_text(wd)
                if strike > 0:
                    ctx.set_source_rgba(0.75, 0.2, 0.12, 0.9); ctx.set_line_width(3.5)
                    ctx.move_to(x - 2, y + fs * 0.68); ctx.line_to(x - 2 + (ww + 4) * strike, y + fs * 0.62); ctx.stroke()
            elif kind == "rep":
                n = int(max(0, reveal - rep_i))
                show = wd[:n]
                rep_i += len(wd) + 1
                if show:
                    src(ctx, rgb("#c27a12")); ctx.show_text(show)
            elif kind == "gold":
                src(ctx, rgb("#c27a12")); ctx.show_text(wd)
                ctx.set_line_width(2.5); ctx.move_to(x, y + fs + 6); ctx.line_to(x + ww, y + fs + 6); ctx.stroke()
            else:
                src(ctx, rgb("#3b2618")); ctx.show_text(wd)
            x += ww + space
        y += lh
    if ref == "THE EXPERIMENT":
        ctx.select_font_face(SERIF, cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(46)
        n = int(reveal)
        s = rep[:n]
        full = ctx.text_extents(rep).x_advance
        ctx.move_to(W / 2 - full / 2, y + 50)
        src(ctx, rgb("#c27a12")); ctx.show_text(s)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def draw_title(ctx, S):
    a = S.get("title", 0)
    if a <= 0:
        return
    ctx.push_group()
    ctx.set_source_rgba(0.05, 0.06, 0.1, 0.62); rrect(ctx, 40, 40, W - 80, 158, 22); ctx.fill()
    ctx.select_font_face(SERIF, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(54)
    for i, line in enumerate(("THE ONE", "READING THIS")):
        ext = ctx.text_extents(line)
        ctx.move_to(W / 2 - ext.x_advance / 2, 104 + i * 60)
        src(ctx, rgb("#f6c560")); ctx.show_text(line)
    ctx.pop_group_to_source(); ctx.paint_with_alpha(a)


def draw_end(ctx, S):
    a = S.get("end", 0)
    if a <= 0:
        return
    ctx.set_source(lin(ctx, 0, 0, 0, H, [(0, (0.03, 0.03, 0.06, 0.25 * a)), (0.55, (0.03, 0.03, 0.06, 0.6 * a)), (1, (0.03, 0.03, 0.06, 0.85 * a))])); ctx.paint()
    ctx.push_group()
    ctx.select_font_face(SERIF, cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(50)
    for i, (line, col) in enumerate((("The one", "#f3e6c8"), ("reading this", "#f6c560"), ("is you.", "#f3e6c8"))):
        ext = ctx.text_extents(line)
        ctx.move_to(W / 2 - ext.x_advance / 2, 830 + i * 64)
        src(ctx, rgb(col)); ctx.show_text(line)
    ctx.pop_group_to_source(); ctx.paint_with_alpha(a)


def vignette(ctx):
    ctx.set_source(rad(ctx, W / 2, H * 0.45, H * 0.35, H * 0.8, [(0, (0, 0, 0, 0)), (1, (0, 0, 0, 0.45))]))
    ctx.paint()
